import asyncio
import time

from opsguardian.strands_advisor import StrandsAdvisor


class Result:
    message = {
        "content": [
            {"text": '{"root_cause":"schema drift","confidence":0.9,"evidence":["tool result"]}'}
        ]
    }


def test_live_strands_call_does_not_block_event_loop(monkeypatch):
    advisor = StrandsAdvisor()
    monkeypatch.setattr("opsguardian.strands_advisor.settings.strands_mode", "bedrock")

    def slow_agent(_prompt):
        time.sleep(0.08)
        return Result()

    monkeypatch.setattr(advisor, "_build_agent", lambda *args, **kwargs: slow_agent)

    async def scenario():
        task = asyncio.create_task(advisor.diagnose({"dataset": "crm.customer_export"}))
        await asyncio.sleep(0.01)
        assert not task.done(), "model invocation blocked the event loop instead of running off-thread"
        result = await task
        assert result["confidence"] == 0.9

    asyncio.run(scenario())
