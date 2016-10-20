#!/bin/bash
EMPTY_STR_CODE=1

ERR_GENERAL=1
ERR_HELP=2
ERR_MALFORMED_COMMAND=3
ERR_PERMISSION=5
ERR_FALLTHROUGH=31
ERR_LIST=50
ERR_APPLICATION=51
ERR_INSTALL=53
ERR_REMOVE=54
ERR_RELOAD=55
ERR_FILE_NOT_FOUND=56
ERR_GIT=57
ERR_DEBUG=100
LOGFILE=opal.log
# LOGFILE=>&2
OPALSERVER=130.207.211.77/opalserver/api/0.1/ #sets OPALSERVER to the default server
OPALSERVER_LIST=http://130.207.211.77:80/opalserver/api/0.1/opals/

##############################################
# lfata : prints a FATAL error message
# Arguments:
#    msg: the message to print
##############################################
lfata() {
  echo "[$(date +'%Y-%m-%dT%H:%M:%S')] FATA: $*" >&2
}

##############################################
# linfo : prints a INFO error message
# Arguments:
#    msg: the message to print
##############################################
linfo () {
  echo "[$(date +'%Y-%m-%dT%H:%M:%S')] INFO: $*" >&2
}

##############################################
# lwarn : prints a WARN error message
# Arguments:
#    msg: the message to print
##############################################
lwarn () {
  echo "[$(date +'%Y-%m-%dT%H:%M:%S')] WARN: $*" >&2
}

##############################################
# nonempty_string: tests a string for emptyness return 0 or ${EMPTY_STR_CODE}
# Allows you to use
# if ! nonempty_string "$ARG" ; then
#    do stuff because ARG is empty
# fi
# slightly more readable than -z
# Globals:
#    none
# Arguments:
#    string : the string to test
##############################################
function nonempty_string () {
    string=$1
    if [ -z "$string" ]; then
        return "${EMPTY_STR_CODE}"
    else
        return 0
    fi
}

##############################################
# if_installed: tests if a program is installed.
# Returns:
#   0 if installeda
#   1 if not installed
#   other if error
# Globals:
#    uses the $PATH
# Arguments:
#    PROG : the name of the program to look for.
##############################################
function if_installed () {
	PROG=$1
	LOCATION=$(which "$PROG")
    retcode=$?
    case $retcode in
    0)
		linfo "$PROG is installed at $LOCATION"
		return 0
        ;;
    1)
		lwarn "$PROG is NOT installed"
		return 1
        ;;
    *)
        lfata "test for $PROG failed $LOCATION"
        return $retcode
    esac
}

##############################################
# ensure_installed: if a program is not available install it.
# Returns:
#   0 if successful
#   other if error in apt-get install
# Globals:
#    uses the $PATH
# Arguments:
#    PROG    : the name of the program to look for.
#    PACKAGE : the name of the package to insall.
##############################################
function ensure_installed (){
	PROG=$1
	PACKAGE=$2
	linfo "checking for $PROG will install $PACKAGE"
	installed=$(if_installed "$PROG")
	if [ $? -eq 1 ]; then
		apt-get install "$PACKAGE"
		return $?
	else
		lwarn "$PROG is already installed: $installed"
	fi
	return 0
}

dpkg_install () {
    f=$1
    linfo "INSTALL: checking for system dependency: $f"
    if [ ! -z "$f" ]; then
        dpkg-query -l "$f" >$LOGFILE
        if [[ "$?" = 1 ]]; then
            linfo "INSTALL: apt-get install $f"
            apt-get install "$f"
        fi
    fi
}

##############################################
# valid_application: checks if the application name is valid and bails if not.
# Returns:
#   0 if successful
#   $ERR_MALFORMED_COMMAND if false
# Globals:
#    none
# Arguments:
#    APPNAME    : the name of the application to validate
##############################################
valid_application () {
    if [ -z "$1" ]; then
        lfata "'opal [install | remove] application <appname>' requires a 3rd argument, the name of the application to remove."
        exit $ERR_MALFORMED_COMMAND
    fi
}

print_help () {
    echo "Use this script to install, remove, reload, or validate opals or to install and remove applications:"
    echo ""
    echo "    $0 install [name of opal to be installed]"
    echo "    $0 remove [name of opal to be removed]"
    echo "    $0 reload [name of opal to be reloaded]"
    echo "    $0 validate [name of opal to be validated]"
    echo ""
    echo "    $0 install application [filepath for application json specification]"
    echo "    $0 remove application [filepath for application json specification]"
    echo ""
    exit $ERR_HELP
}

br_install_help () {
    echo "Usage: $0 install [opal-name]"
    echo "       $0 install application manifest.json"
    echo "  In the 1st form install a single opal"
    echo "  In the 2nd form install a set of opals as described by the manifest in manifest.json"
    echo ""
    exit $ERR_HELP
}

br_reset () {
    OPAL=$1
    if [ -z "$OPAL" ]; then
        linfo "Resetting bedrock..."

        linfo "RESET: removing opals"
        rm analytics/opals/*.py* 2>>$LOGFILE
        rm analytics/*.pyc 2>>$LOGFILE
        touch analytics/opals/__init__.py


        rm dataloader/opals/*.py* 2>>$LOGFILE
        rm dataloader/*.pyc 2>>$LOGFILE
        touch dataloader/opals/__init__.py

        rm visualization/opals/*.py* 2>>$LOGFILE
        rm visualization/*.pyc 2>>$LOGFILE
        touch visualization/opals/__init__.py

        rm ./*.pyc 2>>$LOGFILE

        linfo "RESET: Removing data"
        rm -r analytics/data/*  2>>$LOGFILE
        rm -r dataloader/data/* 2>>$LOGFILE

        linfo "RESET: emptying installed_opals.txt"
        truncate -s 0 installed_opals.txt

        linfo "RESET: dropping mondo databases"
        mongo dataloader --eval "db.dropDatabase();"
        mongo analytics  --eval "db.dropDatabase();"
        mongo visualization --eval "db.dropDatabase();"
    else
        linfo "RESET: reset does not accept an argument"
        exit $ERR_MALFORMED_COMMAND
    fi
    exit 0
}

br_clean () {
    if [ -z "$OPAL" ]; then
        linfo "CLEAN: Cleaning all of bedrock only removes *.pyc use reset to remove source files."

        linfo "CLEAN: removing analytics opals..."
        rm analytics/opals/*.pyc 2>>$LOGFILE
        linfo "CLEAN: removing analytics pyc ..."
        rm analytics/*.pyc 2>>$LOGFILE
        touch analytics/opals/__init__.py

        linfo "CLEAN: removing dataloader opals..."
        rm dataloader/opals/*.pyc 2>>$LOGFILE
        linfo "CLEAN: removing dataloader pyc ..."
        rm dataloader/*.pyc 2>>$LOGFILE
        touch dataloader/opals/__init__.py

        linfo "CLEAN: removing visualization opals ..."
        rm visualization/opals/*.pyc 2>>$LOGFILE
        linfo "CLEAN: removing visualization pyc ..."
        rm visualization/*.pyc 2>>$LOGFILE
        touch visualization/opals/__init__.py

        linfo "CLEAN: removing ./*.pyc"
        rm ./*.pyc 2>>$LOGFILE

    else
        linfo "CLEAN: Cleaning $OPAL..."
        rm "$OPAL"/opals/*.pyc 2>>$LOGFILE
        rm "$OPAL"/*.pyc 2>>$LOGFILE

    fi
    exit 0
}

br_list () {
    if [ "$OPAL" = "installed" ]; then
        linfo "Listing installed opals"
        # TODO This is not json. We should standardize this interface.
        cat installed_opals.txt

    else
        if [ ! -z "$OPAL" ];then
            linfo "LIST: opal list only accepts 'installed' or empty argument"
            exit $ERR_MALFORMED_COMMAND
        fi
        linfo "LIST: Listing avaliable opals"
        linfo "LIST: Available opals from $OPALSERVER:"
        # This is json that comes back from the OPALSERVER
        # you can go to OPALSERVER=130.207.211.77/opalserver/api/0.1/
        # in the browser to see how to use this api command
        curl "$OPALSERVER_LIST" 2>>$LOGFILE # | jq 'keys' to get an actual list.
        if [ $? -ne 0 ]; then
            lfata "LIST: Failed to list opals available at $OPALSERVER (curl error $?)"
            exit $ERR_LIST
        fi
    fi
    exit 0
}

br_reload () {
    linfo "Reloading $OPAL..."

    if [ -z "$OPAL" ]; then
        echo "Usage: $0 reload opalname"
        echo "  re-configures a single opal"
        exit $ERR_MALFORMED_COMMAND
    fi
    if [ ! -z "$3" ]; then
        echo "Usage: $0 reload opalname"
        echo "  re-configures a single opal"
        exit $ERR_MALFORMED_COMMAND
    fi
    #iterate through the units and symlink/install
    for f in $UNITS
    do
        f="$BEDROCK_DIR/$OPAL/$f"
        FILE=$(basename "$f")
        linfo "RELOAD: Symlinking $f"
        echo "python bin/configure.py --mode reload --api $INTERFACE --filename $FILE" > $LOGFILE
        python bin/configure.py --mode reload --api "$INTERFACE" --filename "$FILE"
    done
    service apache2 reload
}

# load the configuration information for an opal.
# if the opal is not cloned, then clone it first.
get_opal_info () {
    LOPALDIR=$OPALDIR/$OPAL
    #see if the directory is there
    #if not, ping the server for metadata and pull down the repo
    if [ ! -d "$LOPALDIR" ]; then
        linfo "OPAL_SETUP: $LOPALDIR is not a directory cloning it."
        exit $ERR_DEBUG
        # get a JSON array containing the currently available OPALs
        OPALS=$(curl --silent $OPALSERVER/opals/) #sets OPALS to the contents of master_config.json
        if [ $? -ne 0 ]; then
            lfata "getinfo: failed to get opal info"
            exit $ERR_INSTALL
        fi
        #data is set to the value of the config.json file
        data=$(echo "$OPALS" | jq --arg key "$OPAL" '.[$key]')
        linfo "data $data"
        if [[ $data = "null" ]]; then
            lfata "APP_SETUP: Server does not provide $OPAL"
            exit $ERR_APPLICATION
        fi
        br_git_clone "$OPALS" "$OPAL"
    fi
    #get the configuration details
    CONFIG_FILE="$LOPALDIR/config.json"
    CONFIG=$(cat "$CONFIG_FILE")
    if [ $? -ne 0 ]; then lfata "could not load configuration json from $CONFIG_FILE"; exit $ERR_FILE_NOT_FOUND; fi
    SUPPORTS=$(echo "$CONFIG" | jq --raw-output '.["'$OPAL'"]'.supports)
    printf "SUPPORTS:\n  %s\n" "$SUPPORTS"
    UNITS=$(echo "$CONFIG" | jq -r '.["'$OPAL'"]'.units)
    linfo "UNITS: $UNITS"
    API=$(echo "$CONFIG" | jq -r '.["'$OPAL'"]'.api)
    INTERFACE=$(echo "$CONFIG" | jq -r --arg key "$OPAL" '.["'$OPAL'"]'.interface)
    linfo "APP_SETUP: Interface: $INTERFACE"

    SCRIPT=$(echo "$CONFIG" | jq -r '.["'$OPAL'"]'.installation_script)

    SYSTEM=$(echo "$CONFIG" | jq --raw-output '.["'$OPAL'"]'.system_dependencies)
    TARGET="/var/www/bedrock/src/$API/opals/"
}

br_remove () {
    COMMAND="$1"
    if [ "$COMMAND" != "remove" ]; then exit $ERR_MALFORMED_COMMAND; fi
    OPAL="$2"
    APPNAME="$3"
    if [ "$OPAL" = "application" ]; then
        valid_application "$APPNAME"
        linfo "REMOVE: Removing application $APPNAME ..."
        OPALS=$(< "$APPNAME" jq -r .opals)

        for o in $OPALS
        do
            # removes internal whitespace in addition to trailing and preceding
            # o="$(echo -e "${o}" | tr -d '[[:space:]]')"
            # recursion to remove each opal in the application.
            linfo "REMOVE: remove command: ./opal.sh remove $o"
            ./opal.sh remove "$o"
        done

    else # "$OPAL" = "application"
        linfo "Removing $OPAL..."
        get_opal_info "$OPAL"
        echo "$TARGET $SYSTEM $SCRIPT $UNITS $CONFIG $SUPPORTS"

        #iterate through the supports and symlink

        for f in $SUPPORTS
        do
            linfo "Processing SUPPORT: $f"
            if ! [ -z "$f" ]; then
                f=$BEDROCK_DIR/$OPAL/$f
                FILE=$(basename "$f")
                echo "    unlinking: $FILE"
                rm "$TARGET$FILE"
            else
                lwarn "REMOVE: Supports: $f"
            fi
        done

        #iterate through the units and symlink/install
        for f in $UNITS
        do
            linfo "Processing UNIT: $f"
            if ! [ -z "$f" ]; then
                f=$BEDROCK_DIR/$OPAL/$f
                MY_PATH=$(readlink -f "$f")
                FILE=$(basename "$f")
                echo "    unlinking: $MY_PATH"
                rm "$TARGET$FILE"
                echo "python bin/configure.py --mode remove --api $INTERFACE --filename $FILE" > $LOGFILE
                python bin/configure.py --mode remove --api "$INTERFACE" --filename "$FILE"
            else
                lwarn "REMOVE: UNITS: $f"
            fi
        done

        # use sed to remove the current opal from the list.
        sed -e "/$OPAL/d" -i installed_opals.txt

    fi
}

br_git_clone () {
    OPALS=$1
    OPAL=$2
    linfo "Cloning: $OPAL"
    HOST=$(echo "$OPALS" | jq -r --arg key "$OPAL" '.[$key]'.host )
    REPO=$(echo "$OPALS" | jq -r --arg key "$OPAL" '.[$key]'.repo )
    TAG=$(echo "$OPALS"  | jq -r --arg key "$OPAL" '.[$key]'.tag  )
    linfo "Gitting r:$REPO from h:$HOST at version v:$TAG"

    # James Fairbanks removed --single-branch so that the opals can be checked out remotely.
    lwarn "TAG is set to:$TAG"
    lwarn "But we are checking out dev because master is broken as of 05/26/2016"
    set -x 
    git clone -b dev "git@$HOST:$REPO" "$BEDROCK_DIR$OPAL"
    set +x
    if [ $? -ne 0 ]  # revert to HTTPS if keys not present
    then
        git clone -b dev "https://$HOST/$REPO" "$BEDROCK_DIR$OPAL"
        retcode=$?
        if [ $retcode -ne 0 ]; then
            lfata "git clone $OPAL failed"
            exit $ERR_GIT
        fi
    fi

}

br_install_application () {
    APPNAME=$1
    # we are operating in application-mode
    # an application is a JSON list of OPALS.
    # we need to read that list and then recursively install each element of the list.
    linfo "INSTALL: Installing application from file $APPNAME.$OPAL.$o"
    valid_application "$APPNAME"
    # TODO bump version of jq
    # then we could use jq 'split(" \t\n")' instead of this hack.
    # TODO Why are we storing a whitespace delimited string inside a JSON file?
    # jq --raw-output prevents jq from escaping the whitespace around the elements of the list.
    OPALS=$( jq --raw-output '.opals' < "$APPNAME" )
    printf "ABOUT TO INSTALL OPALS:\n  %s\n" "$OPALS"
    if [ -z "$OPALS" ]; then
        lwarn "INSTALL: application listed no opals. Check $APPNAME for valid json with key 'opals'"
    fi
    for o in $OPALS
    do
        if [ -z o ]; then
            lwarn "INSTALL: empty opal string"
            continue
        fi
        linfo "INSTALL: Final opal string o: $o"
        linfo "INSTALL Recursion: ./opal.sh install $o"
        ./opal.sh install "$o"
        if [ $? -ne 0 ]; then
            lfata "Failed to install $o"
            exit $ERR_INSTALL
        fi
    done
}

# count=0
# input=""
# br_validate () {
#     for arg in "$@" #move through each argument entered into command line
#     do
#         count=$((count + 1)) #automatically increment the count by 1
#         if [ "$arg" = "--filename" ]; then
#             inputNumber=$((count + 1)) #the arguement after --filepath will be the filepath so increase count by 1 and set to inputNumber
#         fi
#         if [ "$inputNumber" = "$count" ]; then
#             filename="$arg"
#         fi
#     done
#     input=$(echo "$filename" | rev | cut -d/ -f2 | rev) #parse the filename till it only leaves opal-[]-[]
# else
#     input="$OPAL" #input is whatever the normal input would be if not trying to validate
# fi
# }

# br_validate_2 () {
#     if [ "$#" -ne 7 ]; then #there must be 5 arguments following opal.sh
#         echo "ERROR: validate must take exactly three arguments: "
#         echo "      --filename [absolute path for the location of the file]"
#         echo "      --input_directory [absoulte path for location of input files]"
#         echo "      --filter_specs ['{filters}'] or N/A if no filters"
#         exit 0
#     else
#         output_directory="/home/vagrant/bedrock/bedrock-core/validation/OutputStorage/" #the output directory will always be the same because whatever is made gets deleted right away
#         api="$INTERFACE" #using code above able to find the interface without the user having to input it

#         if [ $OPAL = "--filename" ]; then #scenario where --filename is the second argument
#             filename="$( cut -d ' ' -f 3 <<< "$@")" #the actual filename will follow the --filename so the third agrument is made filename
#             input_directory="$( cut -d ' ' -f 5 <<< "$@")" #same reasoning as above
#         elif [ $OPAL = "--input_directory" ]; then #scenario where --input_directory is the second argument
#             input_directory="$( cut -d ' ' -f 3 <<< "$@")" #the actual input_directory will follow the --input_directory so the third agrument is made input_directory
#             filename="$( cut -d ' ' -f 5 <<< "$@")" #same reasoning as above
#         fi
#         #call to validationScript.py that uses the inputs figured out above
#         filter_specs="$7"
#         python /home/vagrant/bedrock/bedrock-core/validation/validationScript.py --api "$api" --filename "$filename" --input_directory "$input_directory" --filter_specs "$filter_specs" --output_directory "$output_directory"
#     fi
# }

if ! [ "$(id -u)" = 0 ]; then
    echo "Please start the script as root or sudo!"
    exit 1
fi
# dpkg is not the only way to install jq.
# dpkg-query -l jq | echo
if ! which jq > "$LOGFILE"; then
    apt-get install jq
fi

if [ -z "$BEDROCK_DIR" ]; then
    # BEDROCK_DIR=/home/vagrant/bedrock/
    # BEDROCK_DIR=~/bedrock/
    BEDROCK_DIR=/var/www/bedrock/
fi

if [ -z "$OPALDIR" ]; then
    OPALDIR=$BEDROCK_DIR/../opals-sources/
fi

linfo "BEDROCK_DIR: $BEDROCK_DIR"

if [ ! -w "$BEDROCK_DIR" ]; then
    lfata "Cannot write to BEDROCK_DIR=$BEDROCK_DIR"
    exit $ERR_PERMISSION
fi
if [ ! -d "$OPALDIR" ]; then
    lfata "Cannot access OPALDIR $OPALDIR"
    exit $ERR_PERMISSION
fi


myln() {
    f=$1
    target=$2
    opal=$3
    FILE=$(basename "$f")
    my_path=$(readlink -f "$f")
    linfo "Linking $opal into $my_path, $target"
    if [ ! -L "$target$FILE" ]; then
        ln -s "$my_path" "$target"
        if [ $? -ne 0 ]; then
            lfata "INSTALL $opal could not make links"
            lfata "    linking: f;$f: FILE;$FILE: MY_PATH;$my_path: target;$target"
            exit $ERR_INSTALL
        fi
    else
        linfo "Linking: $target$FILE was already a link"
    fi
}

br_install () {

    if [ "$OPAL" = "-h" ]; then
        br_install_help

    elif [ "$OPAL" = "application" ]; then
        br_install_application "$3"

    elif ! [ "$OPAL" = "application" ]; then
        get_opal_info "$OPAL"
        echo "Installing from $LOPALDIR"
        echo "$TARGET $SYSTEM $SCRIPT $UNITS $CONFIG $SUPPORTS"
    fi

    linfo "INSTALL $OPAL..."

    #check python dependencies

    #check system dependencies
    if [ -z "$SYSTEM" ]; then
        linfo "INSTALL: no system dependency for: $OPAL"
    fi
    for f in $SYSTEM
    do
        dpkg_install $f
    done


    #execute any necessary additional installation scripts
    if [ -z "$SCRIPT" ]; then
        linfo "INSTALL: no setup scripts for: $OPAL"
    fi
    for f in $SCRIPT
    do
        linfo "INSTALL: running setup script: $f"
        if [ ! -z "$f" ]; then
            cd "$LOPALDIR"
            ./$f
            cd "$BEDROCK_DIR/bedrock-core"
        fi
    done

    #iterate through the supports and symlink
    if [ -z "$SUPPORTS" ]; then
        linfo "INSTALL: no supports for: $OPAL"
    fi
    for f in $SUPPORTS
    do
        if [ ! -z "$f" ]; then
            f="$LOPALDIR/$f"
            myln "$f" "$TARGET" "$OPAL"
        fi
    done


    #iterate through the units and symlink/install
    for f in $UNITS
    do
        if ! [ -z "$f" ]; then
            f=$LOPALDIR/$f
            FILE=""
            myln "$f" "$TARGET" "$OPAL"
            echo "python bin/configure.py --mode add --api $INTERFACE --filename $FILE" > "$LOGFILE"
            python bin/configure.py --mode add --api "$INTERFACE" --filename "$FILE"
            if [ $? -ne 0 ]; then
                lfata "INSTALL: $OPAL : failed to configure $FILE"
                exit $ERR_INSTALL
            fi
        fi
    done

    echo "$OPAL" >> installed_opals.txt
}

# MAIN COMMAND DISPATCH
# you operate this script by passing it a command like
#    opal install opalname
# this ---^^^^^^^              is the COMMAND
# this -----------^^^^^^^      is the OPAL (argument)
COMMAND=$1
OPAL=$2
case "$COMMAND" in
    reset) linfo "PARSING: running $COMMAND"; br_reset "$OPAL" ;;
    list) linfo "PARSING: running $COMMAND"; br_list;;
    clean) linfo "PARSING: running $COMMAND"; br_clean;;
    install) linfo "PARSING: running $COMMAND"; br_install "$@";;
    remove) linfo "PARSING: running $COMMAND"; br_remove "$@";;
    *) print_help "$0"; exit $ERR_HELP ;;
esac
