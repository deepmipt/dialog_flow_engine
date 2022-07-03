import logging


from df_engine.core.keywords import GLOBAL, LOCAL, RESPONSE
from df_engine.core.keywords import TRANSITIONS, PRE_RESPONSE_PROCESSING
from df_engine.core import Context, Actor
import df_engine.labels as lbl
import df_engine.conditions as cnd

from examples import example_1_basics

logger = logging.getLogger(__name__)


def print_function_response(argument: str):
    def response(ctx: Context, actor: Actor, *args, **kwargs):
        return argument

    return response


def create_transitions():
    return {
        ("left", "step_2"): "left",
        ("right", "step_2"): "right",
        lbl.to_start(): "start",  # to start node
        lbl.forward(): "forward",  # to next node in dict
        lbl.backward(): "back",  # to previous node in dict
        lbl.previous(): "previous",  # to previously visited node
        lbl.repeat(): "repeat",  # to the same node
        lbl.to_fallback(): cnd.true(),  # to fallback node
    }


def add_prefix(prefix):
    def add_prefix_processing(ctx: Context, actor: Actor, *args, **kwargs) -> Context:
        processed_node = ctx.current_node
        if not callable(processed_node.response):
            processed_node.response = f"{prefix}: {processed_node.response}"
        elif callable(processed_node.response):
            processed_node.response = f"{prefix}: {processed_node.response(ctx, actor, *args, **kwargs)}"
        ctx.overwrite_current_node_in_processing(processed_node)
        return ctx

    return add_prefix_processing


# a dialog script
script = {
    "root": {
        "start": {RESPONSE: "", TRANSITIONS: {("flow", "step_0"): cnd.true()}},
        "fallback": {RESPONSE: "the end"},
    },
    GLOBAL: {
        PRE_RESPONSE_PROCESSING: {
            "proc_name_1": add_prefix("l1_global"),
            "proc_name_2": add_prefix("l2_global"),
        }
    },
    "flow": {
        LOCAL: {
            PRE_RESPONSE_PROCESSING: {
                "proc_name_2": add_prefix("l2_local"),
                "proc_name_3": add_prefix("l3_local"),
            }
        },
        "step_0": {
            RESPONSE: print_function_response("first"),
            TRANSITIONS: {lbl.forward(): cnd.true()},
        },
        "step_1": {
            PRE_RESPONSE_PROCESSING: {"proc_name_1": add_prefix("l1_step_1")},
            RESPONSE: print_function_response("second"),
            TRANSITIONS: {lbl.forward(): cnd.true()},
        },
        "step_2": {
            PRE_RESPONSE_PROCESSING: {"proc_name_2": add_prefix("l2_step_2")},
            RESPONSE: print_function_response("third"),
            TRANSITIONS: {lbl.forward(): cnd.true()},
        },
        "step_3": {
            PRE_RESPONSE_PROCESSING: {"proc_name_3": add_prefix("l3_step_3")},
            RESPONSE: print_function_response("fourth"),
            TRANSITIONS: {lbl.forward(): cnd.true()},
        },
        "step_4": {
            PRE_RESPONSE_PROCESSING: {"proc_name_4": add_prefix("l4_step_4")},
            RESPONSE: print_function_response("fifth"),
            TRANSITIONS: {"step_0": cnd.true()},
        },
    },
}


actor = Actor(script, start_label=("root", "start"), fallback_label=("root", "fallback"))


# testing
testing_dialog = [
    ("", "l3_local: l2_local: l1_global: first"),
    ("", "l3_local: l2_local: l1_step_1: second"),
    ("", "l3_local: l2_step_2: l1_global: third"),
    ("", "l3_step_3: l2_local: l1_global: fourth"),
    ("", "l4_step_4: l3_local: l2_local: l1_global: fifth"),
    ("", "l3_local: l2_local: l1_global: first"),
]


def run_test():
    ctx = {}
    for in_request, true_out_response in testing_dialog:
        _, ctx = example_1_basics.turn_handler(in_request, ctx, actor, true_out_response=true_out_response)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s-%(name)15s:%(lineno)3s:%(funcName)20s():%(levelname)s - %(message)s",
        level=logging.INFO,
    )
    # run_test()
    example_1_basics.run_interactive_mode(actor)
