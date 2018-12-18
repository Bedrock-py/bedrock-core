import argparse, sys, json

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--opalname', action='store', required=True, metavar='opalname')
    parser.add_argument('--field', action='store', required=False, metavar='field')
    args = parser.parse_args()

    # send request to server, get response
    # right now, lookng up master_conf.json
    with open("../bedrock-opalserver/master_conf.json") as f:
        conf = json.load(f)[args.opalname]
    if args.field:
        print(conf[args.field])
    else:
        print(conf)
