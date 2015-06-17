dpkg-query -l jq | echo
if [[ "$?" = 1 ]]; then
	sudo apt-get install jq
fi

OPALSERVER=130.207.211.77/opalserver/api/0.1/
OPALS=$(sudo curl --silent $OPALSERVER/opals/) #returns all the JSON objects, what it in the master_conf.json

if [ -z "$BEDROCK_DIR" ]; then
	BEDROCK_DIR=~/bedrock/
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

#getting the metadata from the master_conf.json
#jq is a json parser for shell scripting
HOST=$(echo $OPALS | jq '.["'$2'"]'.host) #gets the host information
HOST="${HOST%\"}"
HOST="${HOST#\"}"
REPO=$(echo $OPALS | jq '.["'$2'"]'.repo) #gets the repo information
REPO="${REPO%\"}"
REPO="${REPO#\"}"

SUPPORTS=$(echo $OPALS | jq '.["'$2'"]'.supports)
UNITS=$(echo $OPALS | jq '.["'$2'"]'.units)
API=$(echo $OPALS | jq '.["'$2'"]'.api)
API="${API%\"}"
API="${API#\"}"
INTERFACE=$(echo $OPALS | jq '.["'$2'"]'.interface)
INTERFACE="${INTERFACE%\"}"
INTERFACE="${INTERFACE#\"}"

SCRIPT=$(echo $OPALS | jq '.["'$2'"]'.installation_script)

SYSTEM=$(echo $OPALS | jq '.["'$2'"]'.system_dependencies)

TARGET=/var/www/bedrock/$API/opals/



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

		if [ "$URL" = null ]; then
			echo "ERROR: No opal by that name."
			exit 0
		fi 
		echo "Installing $2..."
		if [ ! -d "$BEDROCK_DIR/$2" ]; then
			git clone -b master --single-branch git@$HOST:$REPO $BEDROCK_DIR$2
			if [ $? -ne 0 ]  # revert to HTTPS if keys not present
			then
			  git clone -b master --single-branch https://$HOST/$REPO $BEDROCK_DIR$2
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
	if [ $2 = "-h" ]; then
		echo "Validate must take in 3 agrugments."
		echo ""
		echo "Argument 1 must be the API that where the file will be insterted."
		echo "Argument 2 must be the absolute path to the file."
		echo "Argument 3 must be the absolute path to any input files needed for the file or NA if the file does not take any inputs."
		echo ""
		exit 0
	elif [ "$#" -ne 4 ]; then
		echo "ERROR: validate must take 4 arguments exactly."
		exit 0
	else
		python /home/vagrant/bedrock/bedrock-core/validation/validationScript.py --api "$2" --filename "$3" --input_directory "$4" --output_directory "/home/vagrant/bedrock/bedrock-core/validation/OutputStorage/"
		#made the last input hard coded because any file that is created is type checked then deleted
	fi
else
    echo "Sorry, there is no script for that option"
fi





#goal is to be able to do ./opal.sh validate opal-analytics-clustering/Kmeans.py 
#and eventually be able to switch between using an absolute path if something does not live on the 7th floor

