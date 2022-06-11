from df_engine.core.keywords import GLOBAL, TRANSITIONS, RESPONSE
from df_engine.core import Context, Actor
import df_engine.conditions as cnd
import df_engine.responses as rsp
import df_engine.labels as lbl
from typing import Union, Optional

#example 4 - transition - what priority

def complex_user_answer_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    request = ctx.last_request
    # the user request can be anything
    return {"some_key": "some_value"} == request

def flow_node_ok_transition(ctx: Context, actor: Actor, *args, **kwargs) -> NodeLabel3Type:
    return ("flow", "node_ok", 1.0)


def high_priority_node_transition(flow_label, label):
    def transition(ctx: Context, actor: Actor, *args, **kwargs) -> NodeLabel3Type:
        return (flow_label, label, 2.0)

    return transition

def upper_case_response(response: str):
    # wrapper for internal response function
    def cannot_talk_about_topic_response(ctx: Context, actor: Actor, *args, **kwargs) -> Any:
        return response.upper()

    return cannot_talk_about_topic_response


def fallback_trace_response(ctx: Context, actor: Actor, *args, **kwargs) -> Any:
    logger.warning(f"ctx={ctx}")
    return {"previous_node": list(ctx.labels.values())[-2], "last_request": ctx.last_request}


def talk_about_topic_response(ctx: Context, actor: Actor, *args, **kwargs) -> Any:
    request = ctx.last_request
    topic_pattern = re.compile(r"(.*talk about )(.*)\.")
    topic = topic_pattern.findall(request)
    topic = topic and topic[0] and topic[0][-1]
    if topic:
        return f"Sorry, I can not talk about {topic} now."
    else:
        return "Sorry, I can not talk about that now."

def talk_about_topic_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    request = ctx.last_request
    return "talk about" in request.lower()
    
    
def no_lower_case_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    request = ctx.last_request
    return "no" in request.lower()

# create script of dialog
script = {
    "global_flow": {
        {"start_node": {RESPONSE: "INITIAL NODE", TRANSITIONS: {
                                                ("flow", "node_hi"): cnd.exact_match("base"),
                                                 "fallback_node": cnd.true()},
         "fallback_node":{RESPONSE:"oops",TRANSITIONS:{lbl.previous():cnd.exact_match("initial"),#to global flow start node
                                                       lbl.repeat():cnd.true()#global flow, fallback node
                                                       }}
                       },
    "flow": {
        "node_hi": {RESPONSE: "Hi!!!",
                   {TRANSITIONS: {("flow", "node_hi"): cnd.exact_match("Hi"),
                           high_priority_node_transition("flow","node_no"): no_lower_case_condition,
                           ("flow","node_topic"):talk_about_topic_condition,
                           ("flow","node_complex"):complex_user_answer_condition,
                           flow_node_ok_transition: cnd.true()}}},
        "node_no": {RESPONSE: upper_case_response("NO"),
                   TRANSITIONS:{lbl.to_fallback(0.1):cnd.true()},#flow,fallback node conf o.1
        "node_complex":{RESPONSE:"Complex condition triggered"},
        "node_topic":{RESPONSE:talk_about_topic_response,
                     TRANSITIONS:{lbl.forward(0.5):cnd.any([cnd.regexp(r"node ok"),cnd.regexp(r"node is ok")]),
                                  lbl.backward(0.5):cnd.regexp(r"node complex")}},
        "node_ok": {RESPONSE: rsp.choice(["OKAY", "OK"])},
        "fallback_node": {  # We get to this node if an error occurred while the agent was running
            RESPONSE: fallback_trace_response,
            TRANSITIONS: {"node_hi": cnd.all([cnd.exact_match("Hi"),cnd.exact_match("Hello")]),
                          "node_ok": cnd.exact_match("Okey")},
        },
    },



}

# init actor
actor = Actor(script, start_label=("flow", "node_hi"))


# handler requests

# turn_handler - a function is made for the convenience of working with an actor
def turn_handler(
    in_request: str, ctx: Union[Context, str, dict], actor: Actor, true_out_response: Optional[str] = None
):
    # Context.cast - gets an object type of [Context, str, dict] returns an object type of Context
    ctx = Context.cast(ctx)
    # Add in current context a next request of user
    ctx.add_request(in_request)
    # pass the context into actor and it returns updated context with actor response
    ctx = actor(ctx)
    # get last actor response from the context
    out_response = ctx.last_response
    # the next condition branching needs for testing
    if true_out_response is not None and true_out_response != out_response:
        msg = f"in_request={in_request} -> true_out_response != out_response: {true_out_response} != {out_response}"
        raise Exception(msg)
    else:
        print(f"in_request={in_request} -> {out_response}")
    return out_response, ctx


# edit this dialog
testing_dialog = [
    ("Hi", "Hi, how are you?"),  # start_node -> node1
    ("i'm fine, how are you?", "Good. What do you want to talk about?"),  # node1 -> node2
    ("Let's talk about music.", "Sorry, I can not talk about music now."),  # node2 -> node3
    ("Ok, goodbye.", "bye"),  # node3 -> node4
    ("Hi", "Hi, how are you?"),  # node4 -> node1
    ("stop", "Ooops"),  # node1 -> fallback_node
    ("stop", "Ooops"),  # fallback_node -> fallback_node
    ("Hi", "Hi, how are you?"),  # fallback_node -> node1
    ("i'm fine, how are you?", "Good. What do you want to talk about?"),  # node1 -> node2
    ("Let's talk about music.", "Sorry, I can not talk about music now."),  # node2 -> node3
    ("Ok, goodbye.", "bye"),  # node3 -> node4
]


def run_test():
    ctx = {}
    for in_request, true_out_response in testing_dialog:
        _, ctx = turn_handler(in_request, ctx, actor, true_out_response=true_out_response)


# interactive mode
def run_interactive_mode(actor):
    ctx = {}
    while True:
        in_request = input("type your answer: ")
        _, ctx = turn_handler(in_request, ctx, actor)

run_test()
print('TESTED WELL')
run_interactive_mode(actor)