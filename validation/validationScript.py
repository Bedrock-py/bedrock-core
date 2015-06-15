from string import punctuation
import argparse
import fnmatch
import os
import shutil
import sys
sys.path.insert(1, '/var/www/analytics-framework/dataloader/python/')
sys.path.insert(1, '/var/www/analytics-framework/analytics/python/')
sys.path.insert(1, '/var/www/analytics-framework/visualization/python/')
sys.path.insert(1, '/var/www/analytics-framework/workflows/python/')

import DataLoader.ingest_utils
import DataLoader.filter_utils
import Analytics.analytics
import Visualization.visualization
from multiprocessing import Queue

def find_imports(fileToCheck, desiredInterface):
	importedList = []
	asterikFound = False
	with open(fileToCheck, 'r') as pyFile:
		for line in pyFile:
			newFront = line.find("import")
			if newFront != -1:
				line = line[newFront + 7:]
				line.split()
				if line.find("*") != -1 and len(line) == 2:
					importedList.extend(line)
				if line.find("*") != -1:
					asterikFound = True
				line =[word.strip(punctuation) for word in line.split()]
				importedList.extend(line)
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
		if "IngestModule" not in importedList and asterikFound == False:
			return "Missing the IngestModule input and * input, can be fixed using 'from ..ingest_utils import IngestModule' and 'from ..utils import *'.\n"
		elif "IngestModule" in importedList and asterikFound == False:
			return "Missing the * input, can be fixed using 'from ..utils import *'.\n"
		elif "IngestModule" not in importedList and asterikFound == False:
			return "Missing the IngestModule input, can be fixed using 'from ..filter_utils import IngestModule'.\n"
		else:
			return ""
	elif desiredInterface == 4:
		if "Filter" not in importedList and asterikFound == False:
			return "Missing the Filter input and * input, can be fixed using 'from ..filter_utils import Filter' and from ..utils import *.\n"
		elif "Filter" in importedList and asterikFound == False:
			return "Missing the * input, can be fixed using 'from ..utils import *'.\n"
		elif "Filter" not in importedList and asterikFound == False:
			return "Missing the Filter input, can be fixed using 'from ..filter_utils import Filter'.\n"
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

	# 	found = False
	# 	i = 0
	# 	while found == False and i < len(returnsList):
	# 		for indReturn in returnsList:
	# 			if indReturn == class_name:
	# 				found = True
	# 				i = len(returnsList)
	# 			i += 1

	# 	if found == False:
	# 		return "File name does not match Class name.\n"
	# 	else:
	# 		return ""
	# else:
	# 	return "File name does not match Class name\n"

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
		elif listOfReturns[0].find("data") == -1 or listOfReturns[0].find("type") == -1 or listOfReturns[0].find("id") == -1:
			return "Missing or incorrectly named return values.\n"
		else:
			return ""
	elif desiredInterface == 3:
		if ("schema" not in listOfReturns and "schemas" not in listOfReturns) or "error" not in listOfReturns or "matrices" not in listOfReturns:
			return "Missing or incorrectly named return values.\n"
		else:
			return ""
	elif desiredInterface == 4:
		if ("True" not in listOfReturns and "False" not in listOfReturns) or ("matrix" not in listOfReturns and "None" not in listOfReturns):
			return "Missing or incorrectly named return values"
		else:
			return ""

def hard_type_check_return(fileToCheck, desiredInterface, my_dir, output_directory):
	specificErrorMessage = ""
	queue = Queue()
	lastOccurence = fileToCheck.rfind("/")
	file_name = fileToCheck[lastOccurence + 1:len(fileToCheck) - 3]
	if desiredInterface == 1:
		file_metaData = Analytics.analytics.get_metadata(file_name)
	elif desiredInterface == 2:
		file_metaData = Visualization.visualization.get_metadata(file_name)
	elif desiredInterface == 3:
		file_metaData = DataLoader.ingest_utils.get_metadata(file_name)
	elif desiredInterface == 4:
		file_metaData = DataLoader.filter_utils.get_metadata(file_name)
	inputList = []
	if desiredInterface != 3 and desiredInterface != 4:
		for elem in file_metaData['inputs']:
			inputList.append(elem)
		inputDict = create_input_dict(my_dir, inputList)
	if desiredInterface == 1:
		count = 0
		computeResult = Analytics.analytics.run_analysis(queue, file_name, file_metaData['parameters'], inputDict, output_directory, "Result")
		
		for file in os.listdir(my_dir):
			if fnmatch.fnmatch(file, "*.csv") or fnmatch.fnmatch(file, ".json"):
				count += 1
		if (count < 1):
			specificErrorMessage += "Missing .csv or .json file, the compute function must create a new .csv or .json file."
		for file_name in os.listdir(output_directory):
			os.remove(os.path.join(output_directory, file_name))
	elif desiredInterface == 2:
		createResult = Visualization.visualization.generate_vis(file_name, inputDict, file_metaData['parameters'])
		if (type(createResult) != dict):
			specificErrorMessage += "Missing a dict return, create function must return a dict item."
	elif desiredInterface == 3:
		posted_data = {
			"matrixFilters": {"Sepal width": [], "Sepal length": []},
			"matrixFeatures":["Sepal width", "Sepal length"],
			"matrixFeaturesOriginal":["Sepal width", "Sepal length"],
			"matrixName":"test",
			"sourceName":"iris",
			"matrixTypes":["Numeric", "Numeric"]
		}

		src = {
			"created": "2015-02-23 22:34:22.060675",
			"host": "127.0.1.1",
			"ingest_id": "Spreadsheet",
			"matrices": [],
			"name": "iris",
			"rootdir": "/var/www/analytics-framework/validation/caa1a3105a22477f8f9b4a3124cd41b6/",
			"src_id": "caa1a3105a22477f8f9b4a3124cd41b6",
			"src_type": "file"
		}

		exploreResult = DataLoader.ingest_utils.explore(file_name, my_dir, [])
		exploreResultList = list(exploreResult)
		typeListExplore = []


		for i in range(len(exploreResultList)):
			typeListExplore.append(type(exploreResultList[i]))
		# for i in range(len(ingestResultList)):
		# 	typeListIngest.append(type(ingestResultList[i]))

		# secondLastOccurence = my_dir.rfind("/", 0, my_dir.rfind("/"))
		# my_dir = my_dir[:secondLastOccurence + 1]
		# for file in os.listdir(my_dir):
		# 	if len(file) > 6:
		# 		shutil.rmtree(my_dir + file + "/")

		if dict in typeListExplore and int not in typeListExplore:
			specificErrorMessage += "Missing a int, explore function must return both a dict and a int."
		elif dict not in typeListExplore and int in typeListExplore:
			specificErrorMessage += "Missing a dict, explore function must return both a dict and a int."
		elif dict not in typeListExplore and int not in typeListExplore:
			specificErrorMessage += "Missing a dict and int, explore function must return both a dict and a int."

		# if bool in typeListIngest and list not in typeListIngest:
		# 	specificErrorMessage += " Missing a list, ingest function must return both a boolean and a list."
		# elif bool not in typeListIngest and list in typeListIngest:
		# 	specificErrorMessage += " Missing a boolean value, ingest function must return both a boolean and a list."
		# elif bool not in typeListIngest and list not in typeListIngest:
		# 	specificErrorMessage += " Missing a boolean value and list, ingest function must return both a boolean and a list."
	elif desiredInterface == 4:
		checkResult = DataLoader.filter_utils.check(file_name, file_metaData['name'], [])
		if type(checkResult) != bool:
			specificErrorMessage += "Missing boolean value, check funtion must return a boolean value"
		
		applyResult = DataLoader.filter_utils.apply(file_name, file_metaData['parameters'], [])
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

print(hard_type_check_return(fileToCheck, desiredInterface, my_dir, output_directory))