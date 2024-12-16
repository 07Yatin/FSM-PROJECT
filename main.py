from flask import Flask, request, jsonify, render_template
import graphviz
import time
app = Flask(__name__)

class FiniteStateMachine:
    def __init__(self, name="FSM"):
        self.dot = graphviz.Digraph(comment=name, format='png')
        self.states = set()
        self.transitions = {}
        self.initial_state = None
        self.final_states = set()

    def add_state(self, state, is_initial=False, is_final=False):
        self.states.add(state)
        if is_initial:
            if self.initial_state:
                raise ValueError(f"Initial state already set to {self.initial_state}")
            self.initial_state = state
            self.dot.node(state, state, style='filled', color='lightblue')
        if is_final:
            self.final_states.add(state)
            self.dot.node(state, state, style='filled', color='lightgreen')
        if not is_initial and not is_final:
            self.dot.node(state, state)

    def add_transition(self, from_state, to_state, symbol):
        if from_state not in self.states or to_state not in self.states:
            raise ValueError("Both states must be added before defining a transition")
        if from_state not in self.transitions:
            self.transitions[from_state] = {}
        if symbol not in self.transitions[from_state]:
            self.transitions[from_state][symbol] = []
        self.transitions[from_state][symbol].append(to_state)
        self.dot.edge(from_state, to_state, label=symbol)

    def process_input(self, input_string):
        if not self.initial_state:
            raise ValueError("No initial state defined")
        current_state = self.initial_state
        for symbol in input_string:
            if (current_state not in self.transitions or
                symbol not in self.transitions[current_state]):
                return False, current_state
            possible_states = self.transitions[current_state][symbol]
            current_state = possible_states[0]
        return current_state in self.final_states, current_state

    def visualize(self, filename='fsm_diagram'):
        return self.dot.render('static/' + filename, cleanup=True)

@app.route('/')
def index():
    return render_template('fsm.html')
@app.route('/nfa2dfa')
def nfa2dfa():
    return render_template('nfsm.html')
@app.route('/simfsm', methods=['POST'])
def simfsm():
    try:
        if request.method == 'POST':
            data = request.json
            n = int(data["n"])
            istate = data["is"]
            fstate = data["fs"]
            trans = data["trans"].split(" ")
            tstring = data["ts"]
            fsm = FiniteStateMachine("FSM Simulator")
            for i in range(n):
                cstate = f"q{i}"
                if cstate == istate and cstate == fstate:
                    fsm.add_state(cstate, is_initial=True, is_final=True)
                elif cstate == istate:
                    fsm.add_state(cstate, is_initial=True)
                elif cstate == fstate:
                    fsm.add_state(cstate, is_final=True)
                else:
                    fsm.add_state(cstate)
            for i in range(len(trans)):
                ctrans = trans[i].split(",")
                fsm.add_transition(ctrans[0], ctrans[2], ctrans[1])
            fsm.visualize()
            res, cfs = fsm.process_input(tstring)
            ctime=str(time.time()).split(".")[0]
            return jsonify({
                "imgpath": f"/static/fsm_diagram.png?{ctime}",
                "result": f"String {tstring} got {'accepted' if res else 'rejected'}, Termination State - {cfs}",
                "success": True,
                "accepted": res
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })
@app.route('/convert', methods=['POST'])
def convert():
    try:
        data = request.json
        n = int(data["n"])
        initial_state = data["is"]
        final_states = set(data["fs"].split())
        transitions = data["trans"].split(" ")
        tstring=data["ts"]
        nfa = FiniteStateMachine("NFA")
        for i in range(n):
            state = f"q{i}"
            nfa.add_state(state, is_initial=(state == initial_state), is_final=(state in final_states))
        for trans in transitions:
            from_state, symbol, to_state = trans.split(",")
            nfa.add_transition(from_state, to_state, symbol)
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
        initial_set = frozenset([initial_state])
        state_queue.append(initial_set)
        dfa.add_state(get_state_name(initial_set), is_initial=True, is_final=bool(initial_set & final_states))
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
                dfa.add_state(next_name, is_final=bool(next_frozen & final_states))
                dfa.add_transition(current_name, next_name, symbol)

                if next_frozen not in visited_states:
                    state_queue.append(next_frozen)
        dfa.visualize("fsm_diagram")
        res, cfs = dfa.process_input(tstring)
        ctime=str(time.time()).split(".")[0]
        return jsonify({
                "imgpath": f"/static/fsm_diagram.png?{ctime}",
                "result": f"String {tstring} got {'accepted' if res else 'rejected'}, Termination State - {cfs}",
                "success": True,
                "accepted": res
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })

if __name__ == "__main__":
    app.run(debug=True)
