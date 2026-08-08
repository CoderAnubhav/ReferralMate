from langgraph.graph import (
    StateGraph,
    START,
    END
)

from .state import ReferralState
from .nodes import (
    analyze_jd,
    generate_referral,
    validate_referral
)


def build_referral_graph(llm):

    graph = StateGraph(
        ReferralState
    )

    graph.add_node(
        "analyze_jd",
        lambda state:
            analyze_jd(state, llm)
    )

    graph.add_node(
        "generate_referral",
        lambda state:
            generate_referral(state, llm)
    )

    graph.add_node(
        "validate_referral",
        validate_referral
    )

    graph.add_edge(
        START,
        "analyze_jd"
    )

    graph.add_edge(
        "analyze_jd",
        "generate_referral"
    )

    graph.add_edge(
        "generate_referral",
        "validate_referral"
    )

    graph.add_edge(
        "validate_referral",
        END
    )

    return graph.compile()