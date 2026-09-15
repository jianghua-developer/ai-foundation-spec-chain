"""交互语义件 → ActionBinding。

DESIGN §1.8 的「结果」层落点：
- `on_success: {goto: SCR#}` → `onSuccess: {navigate: SCR#}`
- `on_failure: [{when, feedback, target}]` → 失败时抛出**规则号**，`onError` 把它写进 state
  （`"$error.message"` 是渲染器的魔值，取抛出异常的 message）；
  反馈则**声明在树里**（Alert + 可见性条件，由 semantics 按 target 锚到字段旁）。

于是「结果」层**完全声明在映射层**：宿主只抛出规则号，不写 state、不写措辞。
"""

from __future__ import annotations

# 渲染器的**内置**动作，不需要宿主实现。
# 导航因此是纯数据：切屏 = 把「当前屏」写进 state，屏的显隐由 visible 条件决定。
SET_STATE = "setState"

# 导航 = **目标屏 + 上下文**，整对象一次写入。
#
# ⚠️ 为什么必须一次写完：实测发现内置动作 `setState` 在 ActionProvider 里走快捷路径并
# **提前 `return`**，`onSuccess` 被整个跳过（静默、不报错）。所以"先写值、再跳转"拆成
# 两步是**不生效**的。写整对象顺带得到一个语义好处：不带上下文的跳转会**清空**上下文。
NAV_PATH = "/nav"


def nav_state(screen: str, context: dict | None = None) -> dict:
    return {"current": screen, "context": context or {}}


def goto(screen: str) -> dict:
    return {"action": SET_STATE, "params": {"statePath": NAV_PATH, "value": nav_state(screen)}}


def failure_state_path(screen_id: str) -> str:
    """失败反馈的落点：当前屏的 failure 槽位。"""
    return f"/{screen_id.lower()}/failure"


def op_call(op: str, *, on_success: dict | None = None,
            on_failure_path: str | None = None, params: dict | None = None) -> dict:
    binding: dict = {"action": op}
    if params:
        binding["params"] = params
    if on_success:
        binding["onSuccess"] = on_success
    if on_failure_path:
        binding["onError"] = {"set": {on_failure_path: "$error.message"}}
    return binding


def failure_visible(screen_id: str, rule: str) -> dict:
    """失败反馈的可见条件：只有失败的正是这条规则时可见。"""
    return {"$state": failure_state_path(screen_id), "eq": rule}


def row_action(act: dict, row: dict) -> dict:
    """行内操作。

    没有 `carry` 就是纯跳转；有 `carry` 则**把这一行的值作为导航上下文一起写**——
    于是目标屏能显示"你点的是哪一条"。值在映射期就确定（行是展开的），所以是字面量。
    """
    carry = act.get("carry")
    if not carry:
        return goto(act["goto"])
    return {
        "action": SET_STATE,
        "params": {
            "statePath": NAV_PATH,
            "value": nav_state(act["goto"], {carry["key"]: row.get(carry["field"], "")}),
        },
    }


def spec_action_binding(action: dict, screen_id: str) -> dict:
    """语义件里的一条 action → ActionBinding。"""
    if "goto" in action and "op" not in action:
        return goto(action["goto"])
    return op_call(
        action["op"],
        # 成功跳转也是纯数据：`{set}` 由渲染器自己执行，宿主不知情
        on_success={"set": {NAV_PATH: nav_state(action["on_success"]["goto"])}} if action.get("on_success") else None,
        on_failure_path=failure_state_path(screen_id) if action.get("on_failure") else None,
    )
