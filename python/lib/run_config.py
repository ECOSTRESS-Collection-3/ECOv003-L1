from xml.etree.ElementTree import parse

class RunConfig(object):
    '''This class does a simple parsing of the run config file supplied
    by PCS.'''
    def __init__(self, fname):
        '''Parse the given run config file.'''
        self.fname = fname
        doc = parse(fname)
        root = doc.getroot()
        if(root.tag != 'input'):
            raise RuntimeException("Don't recognize the root tag in file %s" % fname)
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
        '''Provide a array like interface to gettting data'''
        return self.data[key[0]][key[1]]


        
