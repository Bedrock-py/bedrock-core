/* Variety: A MongoDB Schema Analyzer

This tool helps you get a sense of your application's schema, as well as any 
outliers to that schema. Particularly useful when you inherit a codebase with 
data dump and want to quickly learn how the data's structured. Also useful for 
finding rare keys.

Please see https://github.com/variety/variety for details.

Released by Maypop Inc, © 2012-2014, under the MIT License. */
print('Variety: A MongoDB Schema Analyzer');
print('Version 1.3.0, released 30 May 2014');
print('Modified by GTRI-CTISL for use in BISI');
print('+-------------------------------------+');
print('|          GTRI  PROPRIETARY          |');
print('+-------------------------------------+');

var dbs = [];
var emptyDbs = [];

if (typeof db_name === 'string') {
	db = db.getMongo().getDB( db_name );
}


db.adminCommand('listDatabases').databases.forEach(function(d){
	if(db.getSisterDB(d.name).getCollectionNames().length > 0) {
		dbs.push(d.name);
	}
	if(db.getSisterDB(d.name).getCollectionNames().length === 0) {
		emptyDbs.push(d.name);
	}
});

if (emptyDbs.indexOf(db.getName()) !== -1) {
	throw 'The database specified ('+ db +') is empty.\n'+ 
	'Possible database options are: ' + dbs.join(', ') + '.';
}

if (dbs.indexOf(db.getName()) === -1) {
	throw 'The database specified ('+ db +') does not exist.\n'+ 
	'Possible database options are: ' + dbs.join(', ') + '.';
}

var collNames = db.getCollectionNames().join(', ');
if (typeof collection === 'undefined') {
	throw 'You have to supply a \'collection\' variable, à la --eval \'var collection = "animals"\'.\n'+ 
	'Possible collection options for database specified: ' + collNames + '.\n'+
	'Please see https://github.com/variety/variety for details.';
} 

if (db[collection].count() === 0) {
	throw 'The collection specified (' + collection + ') in the database specified ('+ db +') does not exist or is empty.\n'+ 
	'Possible collection options for database specified: ' + collNames + '.';
}

if (typeof query === 'undefined') { var query = {}; }
print('Using query of ' + tojson(query));

/*  Allow this file to be run from mongo console
Mongo console does not allow return statements, replace with JSONified print statements */
if (typeof runFromPython !== 'boolean') { var runFromPython = false; }

if (typeof limit === 'undefined') { var limit = db[collection].find(query).count(); }
print('Using limit of ' + limit);

if (typeof maxDepth === 'undefined') { var maxDepth = 99; }
print('Using maxDepth of ' + maxDepth);

if (typeof sort === 'undefined') { var sort = {_id: -1}; }
print('Using sort of ' + tojson(sort));



varietyTypeOf = function(thing) {
	if (typeof thing === 'undefined') { throw 'varietyTypeOf() requires an argument'; }

	if (typeof thing !== 'object') {  
		return (typeof thing)[0].toUpperCase() + (typeof thing).slice(1);
	}
	else {
		if (thing && thing.constructor === Array) { 
			return 'Array';
		}
		else if (thing === null) {
			return 'null';
		}
		else if (thing instanceof Date) {
			return 'Date';
		}
		else if (thing instanceof ObjectId) {
			return 'ObjectId';
		}
		else if (thing instanceof BinData) {
			var binDataTypes = {};
			binDataTypes[0x00] = 'generic';
			binDataTypes[0x01] = 'function';
			binDataTypes[0x02] = 'old';
			binDataTypes[0x03] = 'UUID';
			binDataTypes[0x05] = 'MD5';
			binDataTypes[0x80] = 'user';
			return 'BinData-' + binDataTypes[thing.subtype()];
		}
		else {
			return 'Object';
		}
	}
};

function serializeDoc(doc, maxDepth){
  var result = {};
  
  function isHash(v) {
    var isArray = Array.isArray(v);
    var isObject = typeof v === 'object';
    var specialObject = v instanceof Date || 
                      v instanceof ObjectId ||
                      v instanceof BinData;
    return !specialObject && !isArray && isObject;
  }
  
  function serialize(document, parentKey, maxDepth){
    for(var key in document){
      if(!(document.hasOwnProperty(key))) {
        continue;
      }
      var value = document[key];
      result[parentKey+key] = value;
      if(isHash(value) && (maxDepth > 0)) {
        serialize(value, parentKey+key+'.',maxDepth-1);
      }
    }
  }
  serialize(doc, '', maxDepth);
  return result;
}

var interimResults = {}; 
db[collection].find(query).sort(sort).limit(limit).forEach(function(obj) {
	var i=0;

	var flattened = serializeDoc(obj, maxDepth);

	/* Find arrays, break into lists */
	for (var key in flattened){
		if(varietyTypeOf(flattened[key]) == 'Array'){
			for(var i=0;i<flattened[key].length;i++){
				var arrName = key + '[' + i + ']';
				var entry = flattened[key][i];
				/*
				if(runFromPython === false) {
					print(arrName + " " + entry + " " + entry.constructor.name);
				}
				*/
				flattened[arrName] = entry;

				/*
				if(runFromPython === false) {
					var j = flattened[arrName].length-1;
					print(arrName + "["+ j +"] " + flattened[arrName][j].constructor.name);
				}
				*/
			}
		}
	}
	/*print(JSON.stringify(flattened));*/
	for (var key in flattened){
		var value = flattened[key];
		var valueType = varietyTypeOf(value);
		if(!(key in interimResults)){
			var newEntry = {'types':{},'totalOccurrences':1};
			newEntry['types'][valueType] = true;
			interimResults[key] = newEntry;
			if((/boolean|number|string/).test(typeof value)) {
				interimResults[key]['examples'] = [value];
				interimResults[key]['min'] = value;
				interimResults[key]['max'] = value;
			}
		}
		else{
			interimResults[key]['types'][valueType] = true;
			interimResults[key]['totalOccurrences']++;
		}

		var ex = value;

		/* Only compute max/min for scalar values */
		if(['Number','ObjectId','Boolean','String'].indexOf(valueType) !== -1) {
			interimResults[key]['min'] = ex < interimResults[key]['min'] ? ex : interimResults[key]['min'];
			interimResults[key]['max'] = ex > interimResults[key]['max'] ? ex : interimResults[key]['max'];
		} 


		/* Add up to 10 example values */
		if(typeof interimResults[key]['examples'] == 'undefined'){
			interimResults[key]['examples'] = [getStringValue(ex,valueType)];
		} else if (interimResults[key]['examples'].length < 10) {
			ex = getStringValue(ex,valueType);
			if(interimResults[key]['examples'].indexOf(ex) === -1) {
				interimResults[key]['examples'].push(ex);
			}
		}
	}
});


var varietyResults = {};
for(var key in interimResults){
	var entry = interimResults[key];
	var newEntry = {};
	newEntry['_id'] = {'key':key};
	newEntry['value'] = {'types':Object.keys(entry['types'])};
	newEntry['totalOccurrences'] = entry['totalOccurrences'];
	newEntry['percentContaining'] = entry['totalOccurrences']*100/limit;
	newEntry['examples'] = entry['examples'];
	newEntry['range'] = [entry['min'], entry['max']];
	newEntry['suggestion'] = entry['suggestion'];
	varietyResults[key] = newEntry;
}

var resultsDB = db.getMongo().getDB('varietyResults');
var resultsCollectionName = collection + 'Keys';

print('creating results collection: '+resultsCollectionName);
resultsDB[resultsCollectionName].drop();
for(var result in varietyResults) {
	resultsDB[resultsCollectionName].insert(varietyResults[result]); 
}

var numDocuments = db[collection].count();

print('removing leaf arrays in results collection, and getting percentages');
resultsDB[resultsCollectionName].find({}).forEach(function(key) {
	var keyName = key._id.key;

	if(keyName.match(/\.XX$/)) {
		resultsDB[resultsCollectionName].remove({ '_id' : key._id});
		return;
	}

	if(keyName.match(/\.XX/)) {
		keyName = keyName.replace(/.XX/g,'');    
	}

	if(limit < numDocuments) {
		var existsQuery = {};
		existsQuery[keyName] = {$exists: true};
		key.totalOccurrences = db[collection].find(query).count(existsQuery);
	}  
	key.percentContaining = (key.totalOccurrences / numDocuments) * 100.0;
	resultsDB[resultsCollectionName].save(key);
});

var sortedKeys = resultsDB[resultsCollectionName].find({}).sort({totalOccurrences: -1});
var result = [];
sortedKeys.forEach(function(key) {
	if(runFromPython === false) {
		result.push(JSON.stringify(key))
	} else {
		result.push(key)
	}
});

if(runFromPython===true){
	return result;
} else {
	print(result);
}


function serializeDoc(doc, maxDepth){
	var result = {};

	function isHash(v) {
		var isArray = Array.isArray(v);
		var isObject = typeof v === 'object';
		var specialObject = v instanceof Date || 
		v instanceof ObjectId ||
		v instanceof BinData;
		return !specialObject && !isArray && isObject;
	}

	function serialize(document, parentKey, maxDepth){
		for(var key in document){
			if(!(document.hasOwnProperty(key))) {
				continue;
			}
			var value = document[key];
			result[parentKey+key] = value;
			if(isHash(value) && (maxDepth > 0)) {
				serialize(value, parentKey+key+'.',maxDepth-1);
			}
			if(runFromPython === false) {
				/* print(key + ' ' + value); */
			}
		}
	}
	serialize(doc, '', maxDepth);
	return result;
}

function getStringValue(value, valueType){
	retVal = value;
	if(valueType == 'ObjectId'){
		retVal = value.valueOf();
	} else if(valueType == 'Array'){
		retVal = JSON.stringify(value);
	} else if(valueType != 'Number'){
		retVal = String(value);
	}
	return retVal;
}
