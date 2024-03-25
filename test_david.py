
from explainer  import Explainer
from pydavid    import OpenDavid
from dhgraph    import DirectedHypergraph

explainer = Explainer()

OpenDavid.set_david_path("/usr/local/bin/david")
with open("kb.dav", mode="r") as f:
    data = f.read()
    OpenDavid.set_knowledge_base(data)

observation_list = ["say_seer(4, 4)", "vote(3,2)", "say_seer(1,1)",\
                    "vote(5,4)", "say_divined_human(4,1,4)",\
                    "say_divined_werewolf(1,4,1)", "vote(4,3)",\
                    "vote(1,4)", "say_seer(3,3)", "say_divined_human(3,2,3)",\
                    "say_villager(2,2)"]
for atom_str in observation_list:
    explainer.add(atom_str)

#sentence = explainer.explain_possibility("seer(3)")

data = explainer._make_david_problem([atom_str])
OpenDavid.set_problem(data)
json_str = OpenDavid.run()
graph = OpenDavid.build_proofgraph(json_str)
graph.render()

