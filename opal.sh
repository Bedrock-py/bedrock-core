

#get metadata
URL=$(cat ../bedrock-opalserver/master_conf.json | jq '.["'$2'"]'.remote)
URL="${URL%\"}"
URL="${URL#\"}"
SUPPORTS=$(cat ../bedrock-opalserver/master_conf.json | jq '.["'$2'"]'.supports)
UNITS=$(cat ../bedrock-opalserver/master_conf.json | jq '.["'$2'"]'.units)
API=$(cat ../bedrock-opalserver/master_conf.json | jq '.["'$2'"]'.api)
API="${API%\"}"
API="${API#\"}"
INTERFACE=$(cat ../bedrock-opalserver/master_conf.json | jq '.["'$2'"]'.interface)
INTERFACE="${INTERFACE%\"}"
INTERFACE="${INTERFACE#\"}"

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

		echo "Installing $2..."
		if [ ! -d "../$2" ]; then
			git clone $URL ../$2
		fi

		#check python dependencies

		#check system dependencies

		#execute any necessary additional installation scripts

		#iterate through the supports and symlink
		for f in $SUPPORTS
		do
			f="${f%\"}"
			f="${f#\"}"
			f=../$2/$f
  		      if [ ! -z "$f" ]; then
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
		  f=../$2/$f
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

		echo "Removing $2..."
		
		#iterate through the supports and symlink

		for f in $SUPPORTS
		do
		  f="${f%\"}"
		  f="${f#\"}"
		  f=../$2/$f
		  if [ ! -z "$f" ]; then
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
		  f=../$2/$f
		  MY_PATH=$(readlink -f $f)
		  FILE=$(basename $f)
		  echo "    unlinking: $MY_PATH"
		  sudo rm $TARGET$FILE
		  python configure.py --mode remove --api $INTERFACE --filename $FILE
		done

		sudo sed -e /$2/d -i installed_opals.txt

	fi



elif [ $1 = "reload" ]; then
	echo "Reloading $2..."

	#iterate through the units and symlink/install
	for f in $UNITS
	do
	  f="${f%\"}"
	  f="${f#\"}"
	  f=../$2/$f
	  FILE=$(basename $f)
	  python configure.py --mode reload --api $INTERFACE --filename $FILE
	done	

elif [ $1 = "clean" ]; then
	if [ -z $2 ]; then
		echo "Cleaning bedrock..."
		sudo rm analytics/opals/*.pyc 	
		sudo rm analytics/*.pyc 	

		sudo rm dataloader/opals/*.pyc 	
		sudo rm dataloader/*.pyc 	

		sudo rm *.pyc 	



	else
		echo "Cleaning $2..."
		sudo rm $2/opals/*.pyc 	
		sudo rm $2/*.pyc 	

	fi

elif [ $1 = "list" ]; then

	if [ $2 = "installed" ]; then
		cat installed_opals.txt

	else
		echo "Available opals:"
		jq 'keys' ../bedrock-opalserver/master_conf.json
	fi


elif [ $1 = "-h" ]; then
	echo "Use this script to install, remove, or reload opals or to install and remove applications:"
	echo ""
	echo "    ./opal.sh install [name of opal to be installed]"
	echo "    ./opal.sh remove [name of opal to be removed]"
	echo "    ./opal.sh reload [name of opal to be reloaded]"
	echo ""
	echo "    ./opal.sh install application [filepath for application json specification]"
	echo "    ./opal.sh remove application [filepath for application json specification]"
	echo ""
else
    echo "Sorry, there is no script for that option"
fi

