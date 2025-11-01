import uuid

import httpx
from a2a.client import A2AClient, A2ACardResolver
from a2a.types import SendStreamingMessageRequest, MessageSendParams, Message, Role, Part, TextPart


async def main():

    while True:
        user_input = input(">>>: ")
        if user_input == "exit":
            break

        async with httpx.AsyncClient() as httpx_client:
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url="http://localhost:9999"
            )
            agent_card = await resolver.get_agent_card()

            client = A2AClient(
                httpx_client=httpx_client,
                agent_card=agent_card
            )

            message_request = SendStreamingMessageRequest(
                id=str(uuid.uuid4()),
                params=MessageSendParams(
                    message=Message(
                        role=Role.user,
                        message_id=str(uuid.uuid4()),
                        parts=[
                            Part(root=TextPart(text=user_input))
                        ]
                    )
                )
            )

            async for chunk in client.send_message_streaming(message_request):
                print(chunk.root.result.artifact.parts[0].root.text, end="", flush=True)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
