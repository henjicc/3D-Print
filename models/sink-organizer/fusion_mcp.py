"""Small local MCP client with a pre-write resource guard; no background process.

Usage: python3 fusion_mcp.py status
       python3 fusion_mcp.py script /absolute/script.py [readonly]
       python3 fusion_mcp.py read '{"queryType":"document","operation":"open"}'
Use one `with FusionSession() as session:` for a sequence of related operations.
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def resource_state():
    processes = subprocess.run(
        ['pgrep', '-f', 'Autodesk Fusion.app/Contents/MacOS/Autodesk Fusion'],
        capture_output=True, text=True, check=False,
    ).stdout.splitlines()
    if len(processes) != 1:
        raise RuntimeError('Cannot identify exactly one running Fusion process.')
    pid = processes[0]
    output = subprocess.check_output(['lsof', '-nP', '-p', pid, '-Ff'], text=True)
    descriptors = {int(line[1:]) for line in output.splitlines()
                   if line.startswith('f') and line[1:].isdigit()}
    if not descriptors:
        raise RuntimeError('Cannot inspect Fusion resource usage; write cancelled.')
    return {'pid': int(pid), 'count': len(descriptors), 'highest': max(descriptors),
            'free_below_1024': sum(i not in descriptors for i in range(1024))}


def check_write_headroom(state):
    # Project precaution, not an Autodesk guarantee. Never change OS limits.
    if state['highest'] >= 800 or state['free_below_1024'] < 256:
        raise RuntimeError('Fusion resource guard stopped this write: ' + json.dumps(state)
                           + '. Preserve the design, inspect growth, then recover Fusion. '
                           'No write was sent; do not automatically retry.')


class FusionSession:
    def __init__(self, url=None):
        url=url or os.environ.get('FUSION_MCP_URL','http://127.0.0.1:27182/mcp')
        parsed = urllib.parse.urlsplit(url)
        if (parsed.scheme != 'http' or parsed.hostname != '127.0.0.1'
                or parsed.path != '/mcp' or parsed.username or parsed.password
                or parsed.query or parsed.fragment):
            raise ValueError('Only the verified local Fusion MCP endpoint is allowed.')
        self.url, self.sid, self.sequence = url, None, 0
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        self.tools = set()

    def _request(self, body=None, method='POST'):
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json, text/event-stream', 'Connection': 'close'}
        if self.sid:
            headers['Mcp-Session-Id'] = self.sid
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(self.url, data, headers, method=method)
        with self.opener.open(request, timeout=180) as response:
            if response.headers.get('Mcp-Session-Id'):
                self.sid = response.headers['Mcp-Session-Id']
            raw = response.read()
            if not raw:
                return None
            if 'application/json' not in response.headers.get('Content-Type', ''):
                raise RuntimeError('Unexpected MCP transport response; inspect before retrying.')
            result = json.loads(raw)
            if result.get('error'):
                raise RuntimeError('MCP returned an error: ' + json.dumps(result['error']))
            return result.get('result', result)

    def _rpc(self, method, params):
        self.sequence += 1
        return self._request({'jsonrpc': '2.0', 'id': self.sequence,
                              'method': method, 'params': params})

    def __enter__(self):
        resource_state()  # Fail before connecting if the process cannot be inspected.
        try:
            self._rpc('initialize', {'protocolVersion': '2025-03-26', 'capabilities': {},
                                    'clientInfo': {'name': 'sink-organizer-guarded', 'version': '1'}})
            self._request({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
            self.tools = {tool['name'] for tool in self._rpc('tools/list', {})['tools']}
            return self
        except BaseException:
            self.close()
            raise

    def call(self, name, arguments):
        if name not in self.tools:
            raise ValueError('Tool not found in this session: ' + name)
        read_only = name == 'fusion_mcp_read' or (
            name == 'fusion_mcp_execute' and arguments.get('featureType') == 'script'
            and arguments.get('object', {}).get('readOnly') is True)
        if not read_only:
            check_write_headroom(resource_state())
        result = self._rpc('tools/call', {'name': name, 'arguments': arguments})
        if result.get('isError'):
            raise RuntimeError('Fusion tool failed; inspect state before retrying: '
                               + json.dumps(result, ensure_ascii=False))
        for block in result.get('content', []):
            if block.get('type') == 'text':
                try:
                    payload = json.loads(block['text'])
                except (ValueError, TypeError):
                    continue
                if isinstance(payload, dict) and payload.get('success') is False:
                    raise RuntimeError('Fusion operation failed; inspect state before retrying: '
                                       + str(payload.get('error', payload)))
        return result

    def close(self):
        if self.sid:
            try:
                self._request(method='DELETE')
            except urllib.error.HTTPError as error:
                if error.code not in (404, 405):
                    print('MCP session cleanup HTTP status: ' + str(error.code), file=sys.stderr)
            except Exception as error:
                print('MCP session cleanup unconfirmed: ' + type(error).__name__, file=sys.stderr)
            finally:
                self.sid = None

    def __exit__(self, *_):
        self.close()


def main():
    if sys.argv[1:] == ['status']:
        print(json.dumps(resource_state()))
        return
    if len(sys.argv) < 3 or sys.argv[1] not in ('script', 'read'):
        raise SystemExit(__doc__)
    with FusionSession() as session:
        if sys.argv[1] == 'read':
            result = session.call('fusion_mcp_read', json.loads(sys.argv[2]))
        else:
            result = session.call('fusion_mcp_execute', {
                'featureType': 'script', 'object': {
                    'script': Path(sys.argv[2]).read_text(),
                    'readOnly': len(sys.argv) > 3 and sys.argv[3] == 'readonly'}})
        print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
