from typing import Union, Optional, List
import subprocess
import tempfile
import os
import json

from dhgraph import DirectedHypergraph

class OpenDavid:
    """Provides a simple Python Interface of Open-David Version 1.73.

    See: https://github.com/aurtg/open-david/blob/master/manual_en.md .
    """

    _david_path: str     = ""
    """Path to executable file"""
    _knowledge_base: str = ""
    """Knowledge base"""
    _problem: str        = ""
    """Problem"""

    @classmethod
    def set_david_path(cls, path: Union[os.PathLike, str]) -> None:
        """Sets a path to an executable file of Open-David.

        Args:
            path: A path to executable file of Open-David.
        
        Returns:
            None

        Raises:
            ValueError: if no executable file found.
        """
        if not os.access(path, os.X_OK):
            raise ValueError(f"no executable file found: {path}")
        cls._david_path = path

    @classmethod
    def set_knowledge_base(cls, data: str) -> None:
        """Sets a knowledge base data.

        Args:
            data: A knowledge base.

        Returns:
            None

        Raises:
            TypeError:  if data is not a str.
            ValueError: if data is empty.
        """
        if not isinstance(data, str):
            raise TypeError()
        if data == "":
            raise ValueError("empty knowledge base")
        cls._knowledge_base = data 

    @classmethod
    def set_problem(cls, observation_list: List[str],\
        required_atom_list: List[str] = []) -> None:
        """Sets a problem.

        Args:
            observation_list: A list of observations in string format.
            required_atom_list: A list of atoms to be satisfied in solution hypothesis.

        Returns:
            None

        Raises:
            TypeError:  if observation_list is not a list.
            TypeError:  if required_atom_list is not a list.
            TypeError:  if some entry in observation_list is not a str.
            TypeError:  if some entry in required_atom_list is not a str.
            ValueError: if observation_list is empty.
        """
        if not isinstance(observation_list, list)\
            or not isinstance(required_atom_list, list):
            raise TypeError()
        for x in observation_list:
            if not isinstance(x, str):
                raise TypeError()
        for x in required_atom_list:
            if not isinstance(x, str):
                raise TypeError()
        if len(observation_list) == 0:
            raise ValueError("no observation given.")
        data = ""
        data += "problem {\n"
        data += "    observe { "\
            + " ^ ".join(observation_list) + " }\n"
        if len(required_atom_list) > 0:
            data += "    require { "\
                + " ^ ".join(required_atom_list) + " }\n"
        data += "}\n"
        cls._problem = data 
        
    @classmethod
    def run(cls, generator: str = "astar", converter: str = "weighted",\
        solver: str = "scip", enable_pseudo_positive: bool = True,\
        enable_perturbation: bool = True,\
        timeout: Optional[float] = None, max_threads: Optional[int] = None,\
        ) -> str:
        """Runs an Open-David using subprocess module.

        Args:
            generator: An LHS generator: "naive", "simple", "astar".
            converter: an ILP converter: "weighted", "etcetera".
            solver: An ILP solver: "gurobi","lpsolve","cbc","scip".
            enable_pseudo_positive: Whether pseudo-positive option is enabled.
            enable_perturbation: Whether perturbation option is enabled.
            timeout: Timeout in seconds.
            max_threads: The maximum number of threads.

        Returns:
            An output of Open-David in json format.

        Raises:
            CalledProcessError: if subprocess ended with non-zero code.
            TimeoutExpired: if timeout exprired.
        """
        if not os.access(cls._david_path, os.X_OK):
            raise ValueError(f"no executable file found: {cls._david_path}")
        if cls._knowledge_base == "":
            raise Exception("_knowledge_base is not yet set.")
        if cls._problem == "":
            raise Exception("_problem is not yet set.")
        if generator not in ["naive", "simple", "astar"]:
            raise ValueError(f"invalid LHS generator: {generator}")
        if converter not in ["weighted", "etcetera"]:
            raise ValueError(f"invalid ILP converter: {generator}")
        if solver not in ["gurobi","lpsolve","cbc","scip"]:
            raise ValueError(f"invalid ILP solver: {solver}")
            
        with tempfile.TemporaryDirectory() as tempdir:
            with open(f"{tempdir}/in.dav", mode="w") as f:
                f.write("# Knowledge Base\n")
                f.write(cls._knowledge_base)
                f.write("# Problem\n")
                f.write(cls._problem)
            cmd = [cls._david_path,"infer","-C",\
                "-c",f"{generator},{converter},{solver}",\
                "-k",f"{tempdir}/kb",\
                "-o",f"mini:{tempdir}/output"]
            if enable_pseudo_positive:
                cmd.append("--pseudo-positive")
            if max_threads is not None:
                cmd.append("-P f{max_threads}")
            if enable_perturbation:
                cmd.append("-p")
            cmd.append(f"{tempdir}/in.dav")
            res = subprocess.run(cmd, timeout=timeout, capture_output=True,\
                check=True, text=True)
                  
            with open(f"{tempdir}/output", mode="r") as f:
                return f.read()

    @staticmethod
    def build_proofgraph(json_str: str) -> DirectedHypergraph:
        """Builds a proof-graph from an output of Open-David.

        If there are many nodes in the tail of a hyperarc,
        a hyperarc is added per node but with the same label.
        
        Args:
            json_str: An output of Open-David in json format.

        Returns:
            A directed hypergraph.

        Raises:
            TypeError: if json_str is not a str.
        """
        if not isinstance(json_str, str):
            raise TypeError()
        g = DirectedHypergraph()
        json_dict = json.loads(json_str)
        if "results" not in json_dict\
            or len(json_dict["results"]) == 0\
            or "solution" not in json_dict["results"][0]:
            return g  # empty graph if no solution.
        solution = json_dict["results"][0]["solution"]
        if "nodes" not in solution:
            return g
        for item in solution["nodes"]:
            g.add_vertex(item["index"], label=item["atom"])
        if "hypernodes" not in solution:
            return g
        vertices_dict = {item["index"]:tuple(item["nodes"])\
                        for item in solution["hypernodes"]}
        if "edges" not in solution:
            return g
        for item in solution["edges"]:
            head = item["head"]
            tail = item["tail"]
            # Ignore unknown head/tail if exists.
            if head not in vertices_dict\
                or tail not in vertices_dict:
                continue
            # Add a hyperarc per node but with the same label.
            for v in vertices_dict[tail]:
                g.add_hyperarc(vertices_dict[head], v, label=str(item["index"]))
        return g 
