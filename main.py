from flask import Flask, request, jsonify, render_template
import graphviz
import time

app = Flask(__name__)

# FSM Class
class FiniteStateMachine:
    def __init__(self, name="FSM"):
        self.name = name
        self.states = set()
        self.transitions = {}
        self.initial_state = None
        self.final_states = set()
        self.dot = graphviz.Digraph(name, format="png")

    def add_state(self, state, is_initial=False, is_final=False):
        self.states.add(state)
        if is_initial:
            self.initial_state = state
        if is_final:
            self.final_states.add(state)
        self.dot.node(state, state, style="filled", color="lightpink" if is_final else "lightyellow" if is_initial else "grey")

    def add_transition(self, from_state, to_state, symbol):
        self.transitions.setdefault(from_state, {}).setdefault(symbol, []).append(to_state)
        self.dot.edge(from_state, to_state, label=symbol)

    def visualize(self, filename="fsm_diagram"):
        return self.dot.render(f"static/{filename}", cleanup=True)

    def process_input(self, input_string):
        current_state = self.initial_state
        for symbol in input_string:
            if symbol not in self.transitions.get(current_state, {}):
                return False
            current_state = self.transitions[current_state][symbol][0]
        return current_state in self.final_states
    def __str__(self):
        return f"initail {self.initial_state}, {self.final_states}, {self.transitions}, {self.states}"

# Helper Functions
def build_fsm(data):
    fsm = FiniteStateMachine(data.get("name", "FSM"))
    n, initial_state, final_states, transitions = int(data["n"]), data["is"], data["fs"], data["trans"].split("\n")

    # Add states
    for i in range(n):
        state = f"q{i}"
        fsm.add_state(state, is_initial=(state == initial_state), is_final=(state in final_states))

    # Add transitions
    for t in transitions:
        from_state, symbol, to_state = t.split(",")
        fsm.add_transition(from_state, to_state, symbol)
    return fsm


def convert_nfa_to_dfa(nfa,n):
            dfa = FiniteStateMachine("DFA")
            state_counter = 0
            subset_to_name = {}
            state_queue = []
            def get_state_name(subset):
                nonlocal state_counter
                if subset not in subset_to_name:
                    subset_to_name[subset] = f"A{state_counter}"
                    state_counter += 1
                return subset_to_name[subset]
            initial_set = frozenset([nfa.initial_state])
            state_queue.append(initial_set)
            dfa.add_state(get_state_name(initial_set), is_initial=True, is_final=bool(initial_set & nfa.final_states))
            visited_states = set()
            while state_queue:
                current = state_queue.pop(0)
                if current in visited_states:
                    continue
                visited_states.add(current)
                current_name = get_state_name(current)
                symbol_map = {}
                for state in current:
                    for symbol, next_states in nfa.transitions.get(state, {}).items():
                        symbol_map.setdefault(symbol, set()).update(next_states)
                for symbol, next_states in symbol_map.items():
                    next_frozen = frozenset(next_states)
                    next_name = get_state_name(next_frozen)
                    dfa.add_state(next_name, is_final=bool(next_frozen & nfa.final_states))
                    dfa.add_transition(current_name, next_name, symbol)

                    if next_frozen not in visited_states:
                        state_queue.append(next_frozen)
            return dfa


# Flask Routes
@app.route("/")
def index():
    return render_template("fsm.html")


@app.route("/simfsm", methods=["POST"])
def simulate_fsm():
    try:
        data = request.json
        fsm = build_fsm(data)
        fsm.visualize()
        result = fsm.process_input(data["ts"])
        return jsonify({
            "imgpath": f"/static/fsm_diagram.png?{int(time.time())}",
            "result": f"String {'accepted' if result else 'rejected'}",
            "success": True,
            "accepted": result
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/convert", methods=["POST"])
def convert_nfa():
    try:
        data = request.json
        nfa = build_fsm(data)
        n=int(data["n"])
        print(nfa,n)
        dfa = convert_nfa_to_dfa(nfa,n)
        dfa.visualize()
        result = dfa.process_input(data["ts"])
        return jsonify({
            "imgpath": f"/static/fsm_diagram.png?{int(time.time())}",
            "result": f"String {'accepted' if result else 'rejected'}",
            "success": True,
            "accepted": result
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
