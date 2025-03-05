import xml.etree.ElementTree as ET


class RunConfig:
    """This class does a simple parsing of the run config file supplied
    by PCS."""

    def __init__(self, fname):
        """Parse the given run config file."""
        self.fname = fname
        doc = ET.parse(fname)
        root = doc.getroot()
        if root.tag != "input":
            raise RuntimeError("Don't recognize the root tag in file %s" % fname)
        self.data = {}
        for g in root.iterfind("group"):
            gname = g.attrib["name"]
            d = {}
            for s in g.iterfind("scalar"):
                sname = s.attrib["name"]
                d[sname] = s.text
            for v in g.iterfind("vector"):
                vname = v.attrib["name"]
                d[vname] = [e.text for e in v]
            self.data[gname] = d

    def __getitem__(self, key):
        """Provide a array like interface to gettting data"""
        return self.data[key[0]][key[1]]

    def as_list(self, key1, key2):
        """PCS writes a vector of a single element as a scalar. Rather than
        needing to treat this as a special case is the rest of the code, this
        returns a list in all cases, taking a single element and producing
        a list of size 1 if needed."""
        res = self[key1, key2]
        if isinstance(res, list):
            return res
        return [
            res,
        ]


__all__ = ["RunConfig"]
