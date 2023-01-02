#!/bin/bash -l
# This is part of the devconainer-contrib cli 
# For more information: https://github.com/devcontainers-contrib/cli 


set_envs () {
    # Sets up the default values the devcontainer-feature.json has declared for each option
    # This is part of the devconainer-contrib cli 
    # For more information: https://github.com/devcontainers-contrib/cli 

    FILE_NAME=$1
    OPTION_NAMES=($(cat $FILE_NAME | jq -cr '.options | keys[]' |  awk '{ print toupper($0) }'))
    
    # we do this in order to account for empty string values
    OPTION_DEFAULT_VALUES=()
    while read -r line; do 
        OPTION_DEFAULT_VALUES+=("$line") 
    done <<< "$(cat $FILE_NAME | jq -cr '.options[].default')"

    arraylength="${#OPTION_NAMES[@]}"

    for (( i=0; i<${arraylength}; i++ )); do
        current_option=${OPTION_NAMES[i]}
        current_default_value=${DEFAULT_VALUES[i]}

        # setting defaults only if not explicitely given
        if [ -z "${!current_option}" ] ; then
            export $current_option=$current_default_value
        fi
    done
} 
