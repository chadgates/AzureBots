# AzureBots
Deployment of BOTS in Azure

## Bots 3.2 
Has been added to this it is required for installation from source and cannot be installed through PIP.

Source of BOTS 3.2: 
https://sourceforge.net/projects/bots/files/bots%20open%20source%20edi%20software/3.2.0/bots-3.2.0.tar.gz/download


## License
BOTS is licenced under GNU GENERAL PUBLIC LICENSE Version 3; for full text: http://www.gnu.org/copyleft/gpl.html

Henk-Jan Ebbers: http://bots.sourceforge.net/en/index.shtml

Documentation: https://bots-edi.github.io/bots


## Comments

Deployment to Azure as an App Service (Web). 

Various hoops needed to be jumped to get this running and thanks again to all the bloggers, parties that communicated 
about issues that required to be fixed doing this. 


### Tree of problems
Start point was default Azure App Service. 
https://docs.microsoft.com/en-us/azure/python-how-to-install

Local test if WSGI works inspired by this. 
https://blog.cincura.net/233498-cherrypy-on-azure-websites/

Some packages could not be installed from PIP due to missing Visual C++ 2010 installers. 
https://blogs.msdn.microsoft.com/azureossds/2015/06/29/install-native-python-modules-on-azure-web-apps-api-apps/

Thus aimed to install WHL from precompiled binaries, most of them found here: 
http://www.lfd.uci.edu/%7Egohlke/pythonlibs/

However, install failed in default Python version that the Azure App Service installed. It became necessary to install 
an updated version, requiring an own deployment script and the installation of a site-extension.  
https://blogs.msdn.microsoft.com/azureossds/2016/08/25/deploying-django-app-to-azure-app-services-using-git-and-new-version-of-python/
https://blogs.msdn.microsoft.com/pythonengineering/2016/08/04/upgrading-python-on-azure-app-service/

Have used Python 2.7.13 version, however suds-jurko failed to install. Removed the site-extension and used 2.7.12 instead. 
That installed correctly. But now was plagues with IIS failure: 

    ErrorDescription	<handler> scriptProcessor could not be found in <fastCGI> application configuration
    
Fixing came by implementing a applicationHost.xdt file. The deploy.cmd will copy that file to the right site directory after deployment. 
https://github.com/Azure/azure-python-siteextensions/issues/2

As this install is looking to use the bots-jobqueue server, and receive triggers via the Azure Service Bus Queue, 
WebJobs are needed. As per best practise, a retry-communication job is started every 30 minutes. 

