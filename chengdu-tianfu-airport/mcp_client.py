"""Use the already installed Blender MCP over its supported stdio transport."""
import asyncio, json, sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
SERVER = r'C:\Users\JackieTang\AppData\Local\uv\cache\archive-v0\NKT33j3lEMBFC4yF\Scripts\blender-mcp.exe'
async def main():
    async with stdio_client(StdioServerParameters(command=SERVER)) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            name=sys.argv[1]
            args={'user_prompt':'使用 Blender 制作成都天府国际机场建筑作品，导出 GLB 并验证。'}
            if name=='execute_blender_code':args['code']=Path(sys.argv[2]).read_text(encoding='utf-8')
            result=await session.call_tool(name,args)
            for c in result.content:
                if c.type=='text':print(c.text)
                elif c.type=='image':
                    import base64
                    out=Path(__file__).parent/'viewport.png';out.write_bytes(base64.b64decode(c.data));print(out)
asyncio.run(main())
