dpkg-query -l jq | echo
if [[ "$?" = 1 ]]; then
	sudo apt-get install jq
fi


if [ -z "$BEDROCK_DIR" ]; then
	BEDROCK_DIR=~/bedrock/
fi 

OPALSERVER=130.207.211.77/opalserver/api/0.1/ #sets OPALSERVER to the default server
OPALS=$(sudo curl --silent $OPALSERVER/opals/) #sets OPALS to the contents of master_confug.json
REMOTE=true #REMOTE true means that these are not local  
if [ -f "$BEDROCK_DIR$2/config.json" ]; then #if the path has a config.json file it means that this is not part of opalserver already
	OPALS=$(cat $BEDROCK_DIR$2/config.json) #set OPALS to the content of that config.json file
	REMOTE=false #path is local so remote is set to false
fi 


if [ $1 = "-h" ]; then
	echo "Use this script to install, remove, reload, or validate opals or to install and remove applications:"
	echo ""
	echo "    opal install [name of opal to be installed]"
	echo "    opal remove [name of opal to be removed]"
	echo "    opal reload [name of opal to be reloaded]"
	echo "		opal validate [name of opal to be validated]"
	echo ""
	echo "    opal install application [filepath for application json specification]"
	echo "    opal remove application [filepath for application json specification]"
	echo ""
	exit 0

elif [ $1 = "reset" ]; then
        if [ -z $2 ]; then
                echo "Resetting bedrock..."

                sudo rm analytics/opals/*.py* 2>/dev/null
                sudo rm analytics/*.pyc 2>/dev/null
		touch analytics/opals/__init__.py


                sudo rm dataloader/opals/*.py* 2>/dev/null
                sudo rm dataloader/*.pyc 2>/dev/null
		touch dataloader/opals/__init__.py

                sudo rm visualization/opals/*.py* 2>/dev/null
                sudo rm visualization/*.pyc 2>/dev/null
		touch visualization/opals/__init__.py

                sudo rm *.pyc 2>/dev/null

		sudo rm -r analytics/data/*
		sudo rm -r dataloader/data/*

		truncate -s 0 installed_opals.txt

		mongo dataloader --eval "db.dropDatabase();"
		mongo analytics  --eval "db.dropDatabase();"
		mongo visualization --eval "db.dropDatabase();"
        fi
        exit 0

elif [ $1 = "clean" ]; then
	if [ -z $2 ]; then
		echo "Cleaning bedrock..."

		sudo rm analytics/opals/*.pyc 2>/dev/null
		sudo rm analytics/*.pyc 2>/dev/null
		touch analytics/opals/__init__.py

		sudo rm dataloader/opals/*.pyc 2>/dev/null
		sudo rm dataloader/*.pyc 2>/dev/null
		touch dataloader/opals/__init__.py

		sudo rm visualization/opals/*.pyc 2>/dev/null
		sudo rm visualization/*.pyc 2>/dev/null
		touch visualization/opals/__init__.py

		sudo rm *.pyc 2>/dev/null



	else
		echo "Cleaning $2..."
		sudo rm $2/opals/*.pyc 2>/dev/null
		sudo rm $2/*.pyc 2>/dev/null

	fi
	exit 0

elif [ $1 = "list" ]; then

	if [ $2 = "installed" ]; then
		cat installed_opals.txt

	else
		echo "Available opals:"
		curl $OPALSERVER
	fi
	exit 0

fi

count=0
input=""
if [ $1 = "validate" ]; then 
	for arg in "$@" #move through each argument entered into command line
	do
		count=$((count + 1)) #automatically increment the count by 1
		if [ "$arg" = "--filename" ]; then 
			inputNumber=$((count + 1)) #the arguement after --filepath will be the filepath so increase count by 1 and set to inputNumber
		fi
		if [ "$inputNumber" = "$count" ]; then
			filename="$arg"
		fi
	done
	input=$(echo "$filename" | rev | cut -d/ -f2 | rev) #parse the filename till it only leaves opal-[]-[]
else
	input="$2" #input is whatever the normal input would be if not trying to validate
fi


VALID_CONF=true
data=$(echo $OPALS | jq '.["'$input'"]') #data is set to the value of the config.json file
if [[ $data = "null" ]]; then
	VALID_CONF=false
fi

if [ "$VALID_CONF" = true ]; then 
	HOST=$(echo $OPALS | jq '.["'$input'"]'.host)
	HOST="${HOST%\"}"
	HOST="${HOST#\"}"
	REPO=$(echo $OPALS | jq '.["'$input'"]'.repo)
	REPO="${REPO%\"}"
	REPO="${REPO#\"}"

	SUPPORTS=$(echo $OPALS | jq '.["'$input'"]'.supports)
	UNITS=$(echo $OPALS | jq '.["'$input'"]'.units)
	API=$(echo $OPALS | jq '.["'$input'"]'.api)
	API="${API%\"}"
	API="${API#\"}"
	INTERFACE=$(echo $OPALS | jq '.["'$input'"]'.interface)
	INTERFACE="${INTERFACE%\"}"
	INTERFACE="${INTERFACE#\"}"

	SCRIPT=$(echo $OPALS | jq '.["'$input'"]'.installation_script)

	SYSTEM=$(echo $OPALS | jq '.["'$input'"]'.system_dependencies)

	TARGET=/var/www/bedrock/$API/opals/
else
	echo "ERROR: File does not have a valid configuration."
	exit 0
fi

if [ $1 = "install" ]; then

	if [ $2 = "application" ]; then

		echo "Installing application $3..."
		OPALS=$(cat $3 | jq .opals)

		for o in $OPALS
		do
			o="${o%\"}"
			o="${o#\"}"
			o="$(echo -e "${o}" | tr -d '[[:space:]]')"
			./opal.sh install $o
		done

	else
		if [ $2 = "-h" ]; then 
			echo "Two Choices:"
			echo "1: opal install [opal-name]"
			echo "	*This opal must already be installed on the system."
			echo ""
			echo "2. opal install [full filepath to directory]"
			echo "	*This dir must contain a conf.json file with metadata for opal."
			exit 0
		fi
		if [ "$URL" = null ]; then
			echo "ERROR: No opal by that name."
			exit 0
		fi

		echo "Installing $2..."
		if [ "$REMOTE" = true ]; then
			if [ ! -d "$BEDROCK_DIR/$2" ]; then
				git clone -b master --single-branch git@$HOST:$REPO $BEDROCK_DIR$2
				if [ $? -ne 0 ]  # revert to HTTPS if keys not present
				then
			  	git clone -b master --single-branch https://$HOST/$REPO $BEDROCK_DIR$2
				fi
			fi
		fi

		#check python dependencies

		#check system dependencies
		for f in $SYSTEM
		do
		  if ! [ "$f" = "\"\"" ]; then
			f="${f%\"}"
			f="${f#\"}"
			dpkg-query -l $f | echo
			if [[ "$?" = 1 ]]; then
				echo "Installing $f..."
				sudo apt-get install $f
			fi
		  fi
		done	

		
		#execute any necessary additional installation scripts
		for f in $SCRIPT
		do
		  if ! [ "$f" = "\"\"" ]; then
			f="${f%\"}"
			f="${f#\"}"
			cd $BEDROCK_DIR/$2
			./$f
			cd $BEDROCK_DIR/bedrock-core
		  fi
		done	

		#iterate through the supports and symlink
		for f in $SUPPORTS
		do
		  if ! [ "$f" = "\"\"" ]; then
			f="${f%\"}"
			f="${f#\"}"
			f=$BEDROCK_DIR/$2/$f
			FILE=$(basename $f)
			MY_PATH=$(readlink -f $f)
                        if [ ! -L $TARGET$FILE ]; then
			    echo "    linking: $MY_PATH"
			    sudo ln -s $MY_PATH $TARGET
   			fi
		  fi
		done	

		#iterate through the units and symlink/install
		for f in $UNITS
		do
		  if ! [ "$f" = "\"\"" ]; then
		  f="${f%\"}"
		  f="${f#\"}"
		  f=$BEDROCK_DIR/$2/$f
		  MY_PATH=$(readlink -f $f)
		  FILE=$(basename $f)
                  if [ ! -L $TARGET$FILE ]; then
                      echo "    linking: $MY_PATH"
                      sudo ln -s $MY_PATH $TARGET
                  fi
		  python configure.py --mode add --api $INTERFACE --filename $FILE
		  fi
		done	

		echo $2 >> installed_opals.txt

	fi




elif [ $1 = "remove" ]; then
	if [ $2 = "application" ]; then

		echo "Removing application $3..."
		OPALS=$(cat $3 | jq .opals)

		for o in $OPALS
		do
			o="${o%\"}"
			o="${o#\"}"
			o="$(echo -e "${o}" | tr -d '[[:space:]]')"
			./opal.sh remove $o
		done

	else

		if [ "$URL" = null ]; then
			echo "ERROR: No opal by that name."
			exit 0
		fi 
		echo "Removing $2..."
		
		#iterate through the supports and symlink

		for f in $SUPPORTS
		do
		  if ! [ "$f" = "\"\"" ]; then
			  f="${f%\"}"
			  f="${f#\"}"
			  f=$BEDROCK_DIR/$2/$f
		  	  FILE=$(basename $f)
			  echo "    unlinking: $FILE"
		  	  sudo rm $TARGET$FILE
		  fi
		done	

		#iterate through the units and symlink/install
		for f in $UNITS
		do
		  f="${f%\"}"
		  f="${f#\"}"
		  f=$BEDROCK_DIR/$2/$f
		  MY_PATH=$(readlink -f $f)
		  FILE=$(basename $f)
		  echo "    unlinking: $MY_PATH"
		  sudo rm $TARGET$FILE
		  python configure.py --mode remove --api $INTERFACE --filename $FILE
		done

		sudo sed -e /$2/d -i installed_opals.txt

	fi



elif [ $1 = "reload" ]; then
	if [ "$URL" = null ]; then
		echo "ERROR: No opal by that name."
		exit 0
	fi 
	echo "Reloading $2..."

	#iterate through the units and symlink/install
	for f in $UNITS
	do
	  f="${f%\"}"
	  f="${f#\"}"
	  f=$BEDROCK_DIR/$2/$f
	  FILE=$(basename $f)
	  python configure.py --mode reload --api $INTERFACE --filename $FILE
	done	

elif [ $1 = "validate" ]; then
	if [ "$#" -ne 7 ]; then #there must be 5 arguments following opal.sh
		echo "ERROR: validate must take exactly three arguments: "
		echo "		--filename [absolute path for the location of the file]"
		echo "		--input_directory [absoulte path for location of input files]"
		echo "		--filter_specs ['{filters}'] or N/A if no filters"
		exit 0
	else
		output_directory="/home/vagrant/bedrock/bedrock-core/validation/OutputStorage/" #the output directory will always be the same because whatever is made gets deleted right away
		api="$INTERFACE" #using code above able to find the interface without the user having to input it
		
		if [ $2 = "--filename" ]; then #scenario where --filename is the second argument
			filename="$( cut -d ' ' -f 3 <<< "$@")" #the actual filename will follow the --filename so the third agrument is made filename
			input_directory="$( cut -d ' ' -f 5 <<< "$@")" #same reasoning as above
		elif [ $2 = "--input_directory" ]; then #scenario where --input_directory is the second argument
			input_directory="$( cut -d ' ' -f 3 <<< "$@")" #the actual input_directory will follow the --input_directory so the third agrument is made input_directory
			filename="$( cut -d ' ' -f 5 <<< "$@")" #same reasoning as above 
		fi
		#call to validationScript.py that uses the inputs figured out above
		filter_specs="$7"
		python /home/vagrant/bedrock/bedrock-core/validation/validationScript.py --api "$api" --filename "$filename" --input_directory "$input_directory" --filter_specs "$filter_specs" --output_directory "$output_directory"
	fi
else
    echo "Sorry, there is no script for that option"
fi
