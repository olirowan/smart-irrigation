#!/bin/bash

APPLICATION_ENVIRONMENT="production"
APPLICATION_PROJECT="smart-irrigation"
APPLICATION_DIRECTORY="smart-irrigation"

echo "" && echo "Parameters Set:" && echo ""

if [ ! -z "$APPLICATION_ENVIRONMENT" ] ; then
    echo "Environment set to: $APPLICATION_ENVIRONMENT"
else
    echo "Environment not set, exiting."
    exit 1
fi

if [ ! -z "$APPLICATION_PROJECT" ] ; then
    echo "Project set to: $APPLICATION_PROJECT"
else
    echo "Project not set, exiting."
    exit 1
fi

if [ ! -z "$APPLICATION_DIRECTORY" ] ; then
    echo "Directory set to: $APPLICATION_DIRECTORY"
else
    echo "Directory not set, exiting."
    exit 1
fi

echo ""

tar -xzvf /tmp/$APPLICATION_PROJECT.tgz -C /var/www/$APPLICATION_DIRECTORY/ --overwrite || exit 1

# Set permissions and ownership on environment file
chown olirowanxyz:olirowanxyz /var/www/$APPLICATION_DIRECTORY/.env
chmod 664 /var/www/$APPLICATION_DIRECTORY/.env

# Set permissions and recursive owership on install directory
chown -R olirowanxyz:olirowanxyz /var/www/$APPLICATION_DIRECTORY/
chmod 775 /var/www/$APPLICATION_DIRECTORY/

# Remove temporary archive
rm /tmp/$APPLICATION_PROJECT.tgz

# Restart jobs
echo "" && echo "Restarting Supervisor Jobs" && echo ""
supervisorctl stop smart-irrigation-worker
supervisorctl start smart-irrigation-worker

echo "" && echo "Process complete" && echo ""

