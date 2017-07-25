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

    def __str__(self):
        nodes = list(map(lambda x: x['head'], f['nodes']))
        mid = self['_id'] if '_id' in self else ''
        fmt = "_id:%s id:%s name:%s desc:%s nodes:%s"
        return fmt.format(mid, self['id'], self['name'], self['description'], nodes)

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

def flowstr(self):
    nodes = list(map(lambda x: x['head'], f['nodes']))
    mid = self['_id'] if '_id' in self else ''
    fmt = "_id:{} id:{} name:{} desc:{} nodes:{}"
    return fmt.format(mid, self['id'], self['name'], self['description'], nodes)

class Execution(Workflow):
    pass

class WorkflowAPI(object):
    """A handle to a server that can manipulate the Workflows stored in the DB for CRUD."""
    def __init__(self, api):
        """Include a generica BedrockAPI object in this class"""
        self.api = api
    def list(self):
        """list the available workflows from the server"""
        path = self.api.server + "workflows" + "/all"
        resp = requests.get(path)
        print(resp.status_code)
        if resp.status_code != 200:
            raise Exception
        return resp
    def get(self, uid):
        """get a workflow from the server with the specified uid."""
        path = self.api.server + "workflows" + "/" + uid
        return requests.get(path)

    def post(self, wkf):
        """create a new workflow up and return the new uid"""
        path = self.api.server + "workflows" + "/" +"1"
        hdr = {'content-type': 'application/json'}
        return requests.post(path, headers = hdr, data=json.dumps(wkf))

    def put(self, wkf):
        """put a new workflow up and return the new uid"""
        path = self.api.server + "workflows" + "/" +"1"
        hdr = {'content-type': 'application/json'}
        return requests.put(path, headers = hdr, data=wkf)
    def delete(self, uid):
        """Delete a workflow by id"""
        if uid == 'all':
            resps = []
            flows = self.list().json()['workflows']
            for flw in flows:
                resps.append(self.delete(flw['_id']))
            return resps

        path = self.api.server + "workflows" + "/" + uid
        return requests.delete(path)

if __name__ == "__main__":
    from bedrock.client.client import BedrockAPI
    import requests
    
    SERVER = "http://localhost:81/"
    API = WorkflowAPI(BedrockAPI(SERVER))

    # BUNDLES = ['8e9eebbbd85c43f283165b71dd75f204',
    #            '57779eb6dc6e4c38bf008ceb474e3b81',
    #            '98033cc4ed5644d5913b7f46750c24e1',
    #            '14a1a0168891475792321996a0b15b95']
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
    FLTN = Node(NodeMeta(opalclass='filter',
                         description='Filters out low degree vertices',
                         parameters={'comparator':'>',
                                     'colname':'num_neighbors',
                                     'value':0}),
                head='filter_1',
                inputs={'src_id': 0, 'matrix_id':1},
                outputs={'matrix_id': 2})
    LOGITN = Node(NodeMeta('opals.logit2.Logit2.Logit2',
                           'Cooperation over round in each treatment', []),
                  head='log_1', inputs={'src_id':0, 'matrix_id':2}, outputs={'matrix_id':3})
    WFL = Workflow('workflow1', [CSVN, FLTN, LOGITN], BUNDLES, 1, 'Basic Workflow')


    print("These are the available workflows")
    resp = API.list()
    flows = resp.json()['workflows']
    if len(flows) < 1:
        print('No workflows available')
    for f in flows:
        print(flowstr(f))

    print('creating a new workflow')
    putr = API.post(WFL)
    print(putr.text)

    print("These are the available workflows")
    resp = API.list()
    flows = resp.json()['workflows']

    for f in flows:
        print(flowstr(f))

    print('first flow')
    f = flows[0]
    print(flowstr(f))

    print('get a single workflow flow')
    f0 = API.get(f['_id']).json()['workflow']
    print(flowstr(f0))

    fid = f0['_id']
    print('deleting flow: %s'%fid)
    print(API.delete(fid).json())



    # json.dump(WFL, sys.stdout, indent=2)
    # json.dump(WFL.enbundle(), sys.stdout, indent=2)
