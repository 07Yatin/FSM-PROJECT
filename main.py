
from flask import Flask, request, jsonify, render_template
import graphviz
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
        return self.dot.render('static/'+filename, cleanup=True)
@app.route('/')
def index():
    return render_template('fsm.html')
@app.route('/simfsm',methods = ['POST'])
def simfsm():
 try:
    if request.method=='POST':
        data=request.json
        print(data)
        n=int(data["n"])
        istate=data["is"]
        fstate=data["fs"]
        trans=data["trans"].split(" ")
        tstring=data["ts"]
        fsm = FiniteStateMachine("FSM Simulator")
        for i in range(n):
            cstate=f"q{i}"
            if cstate==istate and cstate==fstate:
                fsm.add_state(cstate,is_initial=True,is_final=True)
            elif cstate==istate :
                fsm.add_state(cstate,is_initial=True)
            elif cstate==fstate:
                fsm.add_state(cstate,is_final=True)
            else:
                fsm.add_state(cstate)
        for i in range(len(trans)):
            ctrans=trans[i].split(",")
            fsm.add_transition(ctrans[0],ctrans[2],ctrans[1])
        fsm.visualize()
        res,cfs=fsm.process_input(tstring)
        return jsonify({
            "imgpath": f"/static/fsm_diagram.png",
            "result": f"String {tstring} got {'accepted' if res else 'rejected'}, Termination State - {cfs}",
            "success": True,
            "accepted": res
        })
 except Exception as e:
    return jsonify({
        "success": False,
        "message": str(e)
    })

if __name__=="__main__":
    app.run()