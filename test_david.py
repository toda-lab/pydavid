
from pydavid    import OpenDavid
from dhgraph    import DirectedHypergraph

def _make_david_problem(observation_list, required_atom_list):
    if len(observation_list) == 0:
        raise Exception("no observation")
    res = ""
    res += "problem {\n"
    res += "    observe { "\
        + " ^ ".join(observation_list) + " }\n"
    if len(required_atom_list) > 0:
        res += "    require { "\
            + " ^ ".join(required_atom_list) + " }\n"
    res += "}\n"
    return res

OpenDavid.set_david_path("/usr/local/bin/david")
with open("data/kb.dav", mode="r") as f:
    data = f.read()
    OpenDavid.set_knowledge_base(data)
observation_list = ["say_seer(4, 4)", "vote(3,2)", "say_seer(1,1)",\
                    "vote(5,4)", "say_divined_human(4,1)",\
                    "say_divined_werewolf(1,4)", "vote(4,3)",\
                    "vote(1,4)", "say_seer(3,3)", "say_divined_human(3,2)",\
                    "say_villager(2,2)"]
data = _make_david_problem(observation_list, ["seer(3)"])
OpenDavid.set_problem(data)
json_str = OpenDavid.run()
g = OpenDavid.build_proofgraph(json_str)
g.render(filename="sample", format="png")

