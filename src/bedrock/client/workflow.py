"""
   workflow.py contains the classes necessary to construct workflows and send them to the api server
"""
import json
import sys

class NodeMeta(dict):
    """NodeMeta stores the class, description and parameters of the opal that we are calling"""
    def __init__(self, opalclass, description, parameters):
        super().__init__(self)
        self['opalclass'] = opalclass
        self['description'] = description
        self['parameters'] = parameters

class Node(dict):
    """NodeMeta stores the metadata of the opal that we are calling and the wiring information
    about what data to go in and out of this call to the opal"""
    def __init__(self, meta, head, inputs, outputs, args=[]):
        super().__init__(self)
        if not isinstance(outputs, dict):
            raise TypeError
        if not isinstance(inputs, dict):
            raise TypeError
        self['meta'] = meta
        self['head'] = head
        self['inputs'] = inputs
        self['outputs'] = outputs
        self['args'] = args
    def setoutput(self, bundles, uids):
        "mark the node complete by setting all the bundles with strings"
        for key, val in self['outputs'].items():
            print('%s is ready for %s'%(key, self['head']))
            bundles[val] = uids[key]
        return self
    def isdone(self, bundles):
        """check if all input bundles have been resolved"""
        return all(isinstance(x, str) for x in self['inputs'])





class Workflow(dict):
    """Workflow stores the whole workflow which is a set of nodes and storage spots"""
    def __init__(self, name, nodes, bundles, uid, description):
        super().__init__(self)
        if uid:
            self['id'] = uid
        self['nodes'] = nodes
        self['bundles'] = bundles
        self['description'] = description
        self['name'] = name
    def enbundle(self):
        """replace each input and output with the uuid from bundles"""
        for node in self['nodes']:
            inputs = node['inputs']
            print(inputs)
            for key, val in inputs.items():
                if isinstance(val, str):
                    print('skipping %s already done'%val)
                    continue
                bundles = self['bundles']
                repval = bundles[val]
                if not repval:
                    repval = key
                node['inputs'][key] = repval
        return self
    def execute(self):
        """run the workflow"""
        nodes = self['nodes']
        i = 1
        for node in nodes:
            print('working on %s'%node['head'])
            if node.isdone(self['bundles']):
                print('starting %s'%(node['head']))
                odt = {}
                for key, _ in node['outputs'].items():
                    val = str(i)
                    print('output %s on %s is %s'%(key, node['head'], val))
                    odt[key] = val
                    i += 1
                node.setoutput(self['bundles'], odt)


class Execution(Workflow):
    pass


if __name__ == "__main__":
    BUNDLES = ['8e9eebbbd85c43f283165b71dd75f204',
               '57779eb6dc6e4c38bf008ceb474e3b81',
               '98033cc4ed5644d5913b7f46750c24e1',
               '14a1a0168891475792321996a0b15b95']
    BUNDLES = ['','','','']
    CSVN = Node(NodeMeta(opalclass='opals.spreadsheet.Spreadsheet.Spreadsheet',
                         description='Loads data from CSV or Microsoft Excel spreadsheets.',
                         parameters={
                             'name':'source name'
                         }),
                head='txt_ingest_cooperation_data',
                inputs={},
                outputs={'src_id': 0,
                         'matrix_id': 1})
    FLTN = Node(NodeMeta(opalclass='filter', description='Filters out low degree vertices',
                         parameters={'comparator':'>',
                                     'colname':'num_neighbors',
                                     'value':0}),
                head='filter_1',
                inputs={'src_id': 0, 'matrix_id':1}, #'txt_ingest_cooperation_data'
                outputs={'matrix_id': 2})
    LOGITN = Node(NodeMeta('opals.logit2.Logit2.Logit2',
                           'Cooperation over round in each treatment', []),
                  head='log_1', inputs={'src_id':0, 'matrix_id':2}, outputs={'matrix_id':3})
    WFL = Workflow('workflow1', [CSVN, FLTN, LOGITN], BUNDLES, 1, 'Basic Workflow')
    # json.dump(WFL, sys.stdout, indent=2)
    # json.dump(WFL.enbundle(), sys.stdout, indent=2)
