import subprocess
import tempfile
import os
import json

from dhgraph import DirectedHypergraph

class OpenDavid:
    """Python Interface for Open David Version 1.73"""

    _david_path: str = ""
    """path to executable file"""
    _knowledge_base: str = ""
    """knowledge base"""
    _problem: str = ""
    """problem"""

    @classmethod
    def set_david_path(cls, path: str) -> None:
        cls._david_path = path

    @classmethod
    def set_knowledge_base(cls, lines: str) -> None:
        if lines == "":
            raise Exception("empty knowledge base")
        cls._knowledge_base = lines 

    @classmethod
    def set_problem(cls, lines: str) -> None:
        if lines == "":
            raise Exception("empty problem")
        cls._problem = lines
        
    @classmethod
    def run(cls, generator: str = "astar", converter: str = "weighted",\
        solver: str = "scip", timeout: float = None) -> str:
        if cls._david_path == "":
            raise Exception(f"_david_path is not yet set.")
        if not os.access(cls._david_path, os.X_OK):
            raise Exception(f"no executable file found: {cls._david_path}")
        if cls._knowledge_base == "":
            raise Exception("_knowledge_base is not yet set.")
        if cls._problem == "":
            raise Exception("_problem is not yet set.")
        if not generator in ["naive", "simple", "astar"]:
            raise Exception(f"invalid LHS generator: {generator}")
        if not converter in ["weighted", "etcetera"]:
            raise Exception(f"invalid ILP converter: {generator}")
        if not solver in ["gurobi","lpsolve","cbc","scip"]:
            raise Exception(f"invalid ILP solver: {solver}")
            
        with tempfile.TemporaryDirectory() as tempdir:
            with open(f"{tempdir}/in.dav", mode="w") as f:
                f.write("# Knowledge Base\n")
                f.write(cls._knowledge_base)
                f.write("# Problem\n")
                f.write(cls._problem)
            cmd = [cls._david_path,"infer","-C",\
                "-c",f"{generator},{converter},{solver}",\
                "-k",f"{tempdir}/kb",\
                "-o",f"mini:{tempdir}/output",\
                "--pseudo-positive",\
                f"{tempdir}/in.dav"]
            res = subprocess.run(cmd, timeout=timeout, capture_output=True, check=True, text=True)
                  
            with open(f"{tempdir}/output", mode="r") as f:
                return f.read()

    @staticmethod
    def build_proofgraph(json_str: str) -> DirectedHypergraph:
        g = DirectedHypergraph()
        json_dict = json.loads(json_str)
        solution = json_dict["results"][0]["solution"]
        for item in solution["nodes"]:
            g.add_vertex(item["index"], label=item["atom"])
        vertices_dict = {item["index"]:tuple(item["nodes"])\
                        for item in solution["hypernodes"]}
        for item in solution["edges"]:
            head = item["head"]
            tail = item["tail"]
            assert len(vertices_dict[tail]) == 1
            g.add_hyperarc(vertices_dict[head], vertices_dict[tail][0])
        return g 
