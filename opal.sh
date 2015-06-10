dpkg-query -l jq | echo
if [[ "$?" = 1 ]]; then
	sudo apt-get install jq
fi

OPALSERVER=130.207.211.77/opalserver/api/0.1/opals/
JSON=$(sudo curl --silent $OPALSERVER)

if [ -z "$BEDROCK_DIR" ]; then
	BEDROCK_DIR=~/bedrock/
fi 

if [ $1 = "-h" ]; then
	echo "Use this script to install, remove, or reload opals or to install and remove applications:"
	echo ""
	echo "    opal install [name of opal to be installed]"
	echo "    opal remove [name of opal to be removed]"
	echo "    opal reload [name of opal to be reloaded]"
	echo ""
	echo "    opal install application [filepath for application json specification]"
	echo "    opal remove application [filepath for application json specification]"
	echo ""
	exit 0

elif [ $1 = "clean" ]; then
	if [ -z $2 ]; then
		echo "Cleaning bedrock..."

		sudo rm analytics/opals/*.pyc 2>/dev/null
		sudo rm analytics/*.pyc 2>/dev/null

		sudo rm dataloader/opals/*.pyc 2>/dev/null
		sudo rm dataloader/*.pyc 2>/dev/null

		sudo rm visualization/opals/*.pyc 2>/dev/null
		sudo rm visualization/*.pyc 2>/dev/null

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


HOST=$(echo $JSON | jq '.["'$2'"]'.host)
HOST="${HOST%\"}"
HOST="${HOST#\"}"
REPO=$(echo $JSON | jq '.["'$2'"]'.repo)
REPO="${REPO%\"}"
REPO="${REPO#\"}"

SUPPORTS=$(echo $JSON | jq '.["'$2'"]'.supports)
UNITS=$(echo $JSON | jq '.["'$2'"]'.units)
API=$(echo $JSON | jq '.["'$2'"]'.api)
API="${API%\"}"
API="${API#\"}"
INTERFACE=$(echo $JSON | jq '.["'$2'"]'.interface)
INTERFACE="${INTERFACE%\"}"
INTERFACE="${INTERFACE#\"}"

SCRIPT=$(echo $JSON | jq '.["'$2'"]'.installation_script)

SYSTEM=$(echo $JSON | jq '.["'$2'"]'.system_dependencies)

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
			git clone -b master --single-branch git@$HOST:$REPO $BEDROCK_DIR/$2
			if [ $? -ne 0 ]  # revert to HTTPS if keys not present
			then
			  git clone -b master --single-branch https://$HOST/$REPO $BEDROCK_DIR/$2
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
			MY_PATH=$(readlink -f $f)
			echo "    linking: $MY_PATH"
			sudo ln -s $MY_PATH $TARGET
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
		  echo "    linking: $MY_PATH"
		  sudo ln -s $MY_PATH $TARGET
		  python configure.py --mode add --api $INTERFACE --filename $FILE
		done	

		echo $2 >> installed_opals.txt

	fi




elif [ $1 = "remove" ]; then
	if [ $2 = "application" ]; then

		echo "Installing application $3..."
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

else
    echo "Sorry, there is no script for that option"
fi

