from string import punctuation
import argparse
import fnmatch
import os
import shutil
import sys
import json
sys.path.insert(1, '/var/www/bedrock/')

import analytics.utils
import dataloader.utils
import visualization.utils
from multiprocessing import Queue

#function to determine if the file being checked has the appropriate imports
def find_imports(fileToCheck, desiredInterface):
	importedList = []
	asterikFound = False
	with open(fileToCheck, 'r') as pyFile:
		for line in pyFile:
			newFront = line.find("import") #finds the first occurence of the word import on the line
			if newFront != -1: #an occurence of import has been found
				line = line[newFront + 7:] #sets line to now start at the word after import
				possibleAs = line.find(" as") #used to find import states that have the structure (from x import y as z)
				if possibleAs != -1:
					line = line[possibleAs + 4:]
				if line.find("*") != -1 and len(line) == 2: #if the import is just the *
					importedList.extend(line)
					asterikFound = True
				line =[word.strip(punctuation) for word in line.split()] #correctly splits the inputs based on puncuation
				importedList.extend(line) #creates a single list of all the imports
	if desiredInterface == 1:
		if "Algorithm" not in importedList:
			return "Missing the Algorithm input, can be fixed using 'from ..analytics import Algorithm'.\n"
		else:
			return ""
	elif desiredInterface == 2:
		if "*" not in importedList:
			return "Missing the * input, can be fixed using 'from visualization.utils import *'.\n"
		else:
			return ""
	elif desiredInterface == 3:
		if "*" not in importedList:
			return "Missing the * input, can be fixed using 'from dataloader.utils import *'.\n"
		else:
			return ""
	elif desiredInterface == 4:
		if "*" not in importedList:
			return "Missing the * input, can be fixed using 'from dataloader.utils import *'\n"
		else:
			return ""

def find_class(fileToCheck, desiredInterface):
	classesList = []
	with open(fileToCheck, 'r') as pyFile:
		for line in pyFile:
			newFront = line.find("class")
			newEnd = line.find(")")
			if newFront == 0:
				line = line[newFront + 6: newEnd + 1]
				line.split()
				classesList.append(line)
	return classesList

def find_functions(fileToCheck, desiredInterface):
	functionsList_with_inputs = []
	with open(fileToCheck, 'r') as pyFile:
		for line in pyFile:
			newFront = line.find("def")
			newEnd = line.find(")")
			if newFront != -1:
				line = line[newFront + 3: newEnd + 1]
				line.split()
				functionsList_with_inputs.append(line)
	return functionsList_with_inputs

def compare_fuctions(fileToCheck, desiredInterface):
	fList = find_functions(fileToCheck, desiredInterface)
	if desiredInterface == 1:
		if " __init__(self)" not in fList or " compute(self, filepath, **kwargs)" not in fList:
			return "Function/s and/or specific input/s missing in this file.\n"
		else:
			return ""
	elif desiredInterface == 2:
		if " __init__(self)" not in fList or " initialize(self, inputs)" not in fList or " create(self)" not in fList:
			return "Function/s and/or specific inputs/s missing in this file.\n"
		else:
			return ""
	elif desiredInterface == 3:
		if " __init__(self)" not in fList or " explore(self, filepath)" not in fList or " ingest(self, posted_data, src)" not in fList:
			return "Function/s and/or specific input/s missing in this file.\n"
		else:
			return ""
	elif desiredInterface == 4:
		if " __init__(self)" not in fList or (" check(self, name, sample)" not in fList and " check(self, name, col)" not in fList) or " apply(self, conf)" not in fList:
			return "Function/s and/or specific input/s missing in this file.\n"
		else:
			return ""

def inheritance_check(fileToCheck, desiredInterface):
	class_name_list = find_class(fileToCheck, desiredInterface)
	inhertiance_name = ""
	if (len(class_name_list) > 0):
		if (desiredInterface == 1 and len(class_name_list) > 1):
			inhertiance_name = class_name_list[0]
		elif (len(class_name_list) > 1):
			inhertiance_name = class_name_list[len(class_name_list) - 1]
		else:
			inhertiance_name = class_name_list[0]
		newFront = inhertiance_name.find("(")
		newEnd = inhertiance_name.find(")")
		inhertiance_name = inhertiance_name[newFront + 1:newEnd]

		if desiredInterface == 1:
			if inhertiance_name != "Algorithm":
				return "Class must inherit from the Algorithm super class.\n"
			else:
				return ""
		elif desiredInterface == 2:
			if inhertiance_name != "Visualization":
				return "Class must inherit from the Visualization super class.\n"
			else:
				return ""
		elif desiredInterface == 3:
			if inhertiance_name != "Ingest":
				return "Class must inherit from the Ingest super class.\n"
			else:
				return ""
		elif desiredInterface == 4:
			if inhertiance_name != "Filter":
				return "Class must inherit from the Filter super class.\n"
			else:
				return ""
	else:
		return "There are no classes in this file.\n"

def validate_file_name(fileToCheck, desiredInterface):
	class_name_list = find_class(fileToCheck, desiredInterface)
	class_name = ""
	if (len(class_name_list) > 0):
		if (desiredInterface == 1 and len(class_name_list) > 1):
			class_name = class_name_list[0]
		elif (len(class_name_list) > 1):
			class_name = class_name_list[len(class_name_list) - 1]
		else:
			class_name = class_name_list[0]
		trim = class_name.find("(")
		class_name = class_name[:trim]
		returnsList = list_returns(fileToCheck, desiredInterface)

		superStament = []
		with open(fileToCheck, 'r') as pyFile:
			for line in pyFile:
				newFront = line.find("super")
				if newFront != -1:
					trimFront = line.find("(")
					trimBack = line.find(",")
					line = line[trimFront + 1: trimBack]
					superStament.append(line)
		if class_name not in superStament:
			return "File name does not match Class name\n"
		else:
			return ""

def list_returns(fileToCheck, desiredInterface):
	returnsList = []
	newLine = ""
	with open(fileToCheck, 'r') as pyFile:
		for line in pyFile:
			if line.find("#") == -1:
				newFront = line.find("return")
				if newFront != -1:
					possibleErrorMessageCheck1 = line.find("'")
					bracketBefore = line.find("{")
					lastBracket = line.find("}")
					newLine = line[possibleErrorMessageCheck1:]
					possibleErrorMessageCheck2 = newLine.find(" ")
					if possibleErrorMessageCheck2 == -1:
						line = line[newFront + 7:]
						line.split()
						line = [word.strip(punctuation) for word in line.split()]
						returnsList.extend(line)
					elif possibleErrorMessageCheck1 == bracketBefore + 1:
						line = line[newFront + 7:lastBracket + 1]
						line.split()
						returnsList.append(line)
	return returnsList

def check_return_values(fileToCheck, desiredInterface):
	listOfReturns = list_returns(fileToCheck, desiredInterface)
	listOfClasses = find_class(fileToCheck, desiredInterface)
	firstElement = listOfClasses[0]
	for elem in listOfClasses:
		cutOff = elem.find("(")
		if cutOff != -1:
			elem = elem[:cutOff]
			firstElement = elem
	listOfClasses[0] = firstElement
	if desiredInterface == 1:
		listOfFunctions = find_functions(fileToCheck, desiredInterface)
		if len(listOfFunctions) == 2 and len(listOfReturns) > 0:
			return "Too many return values in this file.\n"
		else:
			return ""
	elif desiredInterface == 2:
		if len(listOfReturns) > 1:
			if listOfClasses[0] not in listOfReturns or listOfReturns[1].find("data") == -1 or listOfReturns[1].find("type") == -1 or listOfReturns[1].find("id") == -1:
				return "Missing or incorrectly named return values.\n"
			else: 
				return ""
		elif listOfReturns[0].find("data") == -1 or listOfReturns[0].find("type") == -1 or listOfReturns[0].find("id") == -1:
			return "Missing or incorrectly named return values.\n"
		else:
			return ""
	elif desiredInterface == 3:
		if ("schema" not in listOfReturns and "schemas" not in listOfReturns and "collection:ret" not in listOfReturns) or "error" not in listOfReturns or "matrices" not in listOfReturns:
			return "Missing or incorrectly named return values.\n"
		else:
			return ""
	elif desiredInterface == 4:
		if ("True" not in listOfReturns and "False" not in listOfReturns) or ("matrix" not in listOfReturns and "None" not in listOfReturns):
			return "Missing or incorrectly named return values"
		else:
			return ""

def hard_type_check_return(fileToCheck, desiredInterface, my_dir, output_directory, filter_specs):
	specificErrorMessage = ""
	queue = Queue()
	lastOccurence = fileToCheck.rfind("/")
	file_name = fileToCheck[lastOccurence + 1:len(fileToCheck) - 3]
	print filter_specs
	if desiredInterface == 1:
		file_metaData = analytics.utils.get_metadata(file_name)
	elif desiredInterface == 2:
		file_metaData = visualization.utils.get_metadata(file_name)
	elif desiredInterface == 3:
		file_metaData = dataloader.utils.get_metadata(file_name, "ingest")
	elif desiredInterface == 4:
		file_metaData = dataloader.utils.get_metadata(file_name, "filters")
	inputList = []
	if desiredInterface != 3 and desiredInterface != 4:
		for elem in file_metaData['inputs']:
			inputList.append(elem)
		inputDict = create_input_dict(my_dir, inputList)
	if desiredInterface == 1:
		count = 0
		computeResult = analytics.utils.run_analysis(queue, file_name, file_metaData['parameters'], inputDict, output_directory, "Result")

		for file in os.listdir(my_dir):
			if fnmatch.fnmatch(file, "*.csv") or fnmatch.fnmatch(file, ".json"):
				count += 1
		if (count < 1):
			specificErrorMessage += "Missing .csv or .json file, the compute function must create a new .csv or .json file."
		for file_name in os.listdir(output_directory):
			os.remove(os.path.join(output_directory, file_name))
	elif desiredInterface == 2:
		createResult = visualization.utils.generate_vis(file_name, inputDict, file_metaData['parameters'])
		if (type(createResult) != dict):
			specificErrorMessage += "Missing a dict return, create function must return a dict item."
	elif desiredInterface == 3:
		filter_specs_dict = json.loads(str(filter_specs))
		exploreResult = dataloader.utils.explore(file_name, my_dir, [])
		exploreResultList = list(exploreResult)
		count = 0
		typeOfMatrix = []
		matrix = ""
		nameOfSource = ""
		filterOfMatrix = []
		for elem in exploreResult:
			if type(elem) == dict:
				for key in elem.keys():
					nameOfSource = str(key)
				if len(elem.values()) == 1:
					for value in elem.values():
						while count < len(value):
							for item in value[count].keys():
								if item == "type":
									matrix = str(value[count]['type'])
									matrix = matrix[2:len(matrix) - 2]
									typeOfMatrix.append(matrix)
								if item == "key_usr":
									filterOfMatrix.append(str(value[count]['key_usr']))
							count += 1
		typeListExplore = []
		posted_data = {
			'matrixFilters':{},
			'matrixFeatures':[],
			'matrixFeaturesOriginal':[],
			'matrixName':"test",
			'sourceName':nameOfSource,
			'matrixTypes':[]
		}

		# posted_data['matrixFilters'].update({filterOfMatrix[0]:{"classname":"DocumentLEAN","filter_id":"DocumentLEAN","parameters":[],"stage":"before","type":"extract"}}) #for Text
		# posted_data['matrixFilters'].update({filterOfMatrix[0]:{"classname":"TweetDocumentLEAN","filter_id":"TweetDocumentLEAN","parameters":[{"attrname":"include","name":"Include the following keywords","type":"input","value":""},{"attrname":"sent","value":"No"},{"attrname":"exclude","name":"Exclude the following keywords","type":"input","value":""},{"attrname":"lang","name":"Language","type":"input","value":""},{"attrname":"limit","name":"Limit","type":"input","value":"10"},{"attrname":"start","name":"Start time","type":"input","value":""},{"attrname":"end","name":"End time","type":"input","value":""},{"attrname":"geo","name":"Geo","type":"input","value":""}],"stage":"before","type":"extract"}}) #for Mongo
		posted_data['matrixFilters'].update({filterOfMatrix[0]:filter_specs_dict})

		# posted_data['matrixFilters'].update({filterOfMatrix[0]:{}}) #for spreadsheet

		posted_data['matrixFeatures'].append(filterOfMatrix[0])
		posted_data['matrixFeaturesOriginal'].append(filterOfMatrix[0])
		posted_data['matrixTypes'].append(typeOfMatrix[0])

		secondToLastOccurence = my_dir.rfind("/", 0, my_dir.rfind("/"))
		my_dir = my_dir[:secondToLastOccurence + 1]
		src = {
			'created':dataloader.utils.getCurrentTime(),
			'host': "127.0.1.1",
			'ingest_id':file_name,
			'matrices':[],
			'name': nameOfSource,
			'rootdir':my_dir,
			'src_id': "test_files",
			'src_type':"file"
		}

		ingestResult = dataloader.utils.ingest(posted_data, src)
		ingestResultList = list(ingestResult)
		typeListIngest = []
		for i in range(len(exploreResultList)):
			typeListExplore.append(type(exploreResultList[i]))
		for i in range(len(ingestResultList)):
			typeListIngest.append(type(ingestResultList[i]))

		for file in os.listdir(my_dir):
			if os.path.isdir(my_dir + file) and len(file) > 15:
				shutil.rmtree(my_dir + file + "/")
			if file.startswith("reduced_"):
				os.remove(os.path.join(my_dir, file))

		if dict in typeListExplore and int not in typeListExplore:
			specificErrorMessage += "Missing a int, explore function must return both a dict and a int."
		elif dict not in typeListExplore and int in typeListExplore:
			specificErrorMessage += "Missing a dict, explore function must return both a dict and a int."
		elif dict not in typeListExplore and int not in typeListExplore:
			specificErrorMessage += "Missing a dict and int, explore function must return both a dict and a int."

		if bool in typeListIngest and list not in typeListIngest:
			specificErrorMessage += " Missing a list, ingest function must return both a boolean and a list."
		elif bool not in typeListIngest and list in typeListIngest:
			specificErrorMessage += " Missing a boolean value, ingest function must return both a boolean and a list."
		elif bool not in typeListIngest and list not in typeListIngest:
			specificErrorMessage += " Missing a boolean value and list, ingest function must return both a boolean and a list."
	elif desiredInterface == 4:

		conf = {
			'mat_id':'27651d66d4cf4375a75208d3482476ac',
			'storepath':'/home/vagrant/bedrock/bedrock-core/caa1a3105a22477f8f9b4a3124cd41b6/source/',
			'src_id':'caa1a3105a22477f8f9b4a3124cd41b6',
			'name':'iris'
		}
		checkResult = dataloader.utils.check(file_name, file_metaData['name'], conf)
		if type(checkResult) != bool:
			specificErrorMessage += "Missing boolean value, check funtion must return a boolean value."

		applyResult = dataloader.utils.apply(file_name, file_metaData['parameters'], conf)
		if type(applyResult) != dict:
			specificErrorMessage += " Missing a dict object, apply function must return a dict object."
	return specificErrorMessage

def create_input_dict(my_dir, inputList):
	returnDict = {}
	i = 0
	j = 1
	length = len(inputList)
	for file in os.listdir(my_dir):
		if file in inputList:
			if length == 1 or (length > 1 and file != inputList[length - 1]) or (length > 1 and inputList[i] != inputList[i + 1]):
				returnDict.update({file:{'rootdir':my_dir}})
			elif length > 1 and inputList[i] == inputList[i + 1]:
				firstNewFile = file + "_" + str(j)
				j += 1
				returnDict.update({firstNewFile:{'rootdir':my_dir}})

			if j > 1:
				secondNewFile = file + "_" + str(j)
				returnDict.update({secondNewFile:{'rootdir':my_dir}})
			i += 1
			length -= 1
	return returnDict

parser = argparse.ArgumentParser(description="Validate files being added to system.")
parser.add_argument('--api', help="The API where the file is trying to be inserted.", action='store', required=True, metavar='api')
parser.add_argument('--filename', help="Name of file inlcuding entire file path.", action='store', required=True, metavar='filename')
parser.add_argument('--input_directory', help="Directory where necessary inputs are stored", action='store', required=True, metavar='input_directory')
parser.add_argument('--filter_specs', help="Specifications for a used filter.", action='store', required=True, metavar='filter_specs')
parser.add_argument('--output_directory', help='Directory where outputs are stored (type NA if there will be no outputs).', action='store', required=True, metavar='output_directory')
args = parser.parse_args()

desiredInterface = 0
fileToCheck = args.filename

if args.api.lower() == "analytics":
	desiredInterface = 1
elif args.api.lower() == "visualization":
	desiredInterface = 2
elif args.api.lower() == "ingest":
	desiredInterface = 3
elif args.api.lower() == "filter":
	desiredInterface = 4

my_dir = args.input_directory
output_directory = args.output_directory
filter_specs = args.filter_specs

errorMessage = ""
errorMessage += str(find_imports(fileToCheck, desiredInterface))
errorMessage += str(compare_fuctions(fileToCheck, desiredInterface))
errorMessage += str(inheritance_check(fileToCheck, desiredInterface))
errorMessage += str(validate_file_name(fileToCheck, desiredInterface))
errorMessage += str(check_return_values(fileToCheck, desiredInterface))
if len(errorMessage) == 0:
	print("File has been validated and is ready for input")
else:
	print("Error Log: ")
	print(errorMessage)

print(hard_type_check_return(fileToCheck, desiredInterface, my_dir, output_directory, filter_specs))

