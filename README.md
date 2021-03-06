# AzureBots
Deployment of BOTS in Azure

To get started with the deployment of a python app as an App Service, follow this guide, which also covers pushing
updates via GIT to the build process:
https://docs.microsoft.com/en-us/azure/app-service/app-service-web-get-started-python


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

This install is not with an activated job queue as described below. In order to activate the job-queue, the
content of App_data/jobs must be replaced with the required items from azurebots/App_data_optional/jobs and 
the bots.ini must be adjusted to contain the correct settings (enable jobqueueserver and define the type).


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

But now was plagues with IIS failure: 

    ErrorDescription	<handler> scriptProcessor could not be found in <fastCGI> application configuration
    
Fixing came by implementing a applicationHost.xdt file. The deploy.cmd will copy that file to the right site directory after deployment. 
https://github.com/Azure/azure-python-siteextensions/issues/2

The bots-engine could not be started from bots monitor. The reason is that subprocess is started by the python executable 
that is outside of the virtual environment and therefore the path to bots is not known. web.config needed to adjustement
to contain the path to the packages where bots is located: 

    <add key="PYTHONPATH" value="D:\home\site\wwwroot;D:\home\site\wwwroot\env\Lib\site-packages" />

Bots allows to create an "index.py" file that contains all settings. However, the wfastcgi script contains a 
file_handler that monitors any changes to "*.py" files and then restarts the process. Therefore, I have changed
the filename output to "index.py.txt" in views.py, and fixed another typo. 


## Jobqueues
As this install is looking to use the bots-jobqueue server, and receive triggers via the Azure Service Bus Queue, 
WebJobs are needed. As per best practise, a retry-communication job is started every 30 minutes.
http://blog.amitapple.com/post/74215124623/deploy-azure-webjobs/
http://withouttheloop.com/articles/2015-06-23-deploying-custom-services-as-azure-webjobs/


### Bots-Jobqueue-Server 
Unfortunately, the XML-RPC Job Queue Server will not work in Azure App Service. Have tried multiple options which you will find in this repository.
The main issue is that one process cannot talk to another process over localhost:someother port unless they are 
in the same sandbox. But even that did not work for me - I tries to spawn the XMLRPC server in the app.py (which worked locally), 
but I never got to make it work on Azure. Some infos here:
https://github.com/projectkudu/kudu/wiki/Azure-Web-App-sandbox

As a result, I ditched the jobqueue server completely and made BOTS take jobs/put jobs only via the Azure Service Bus. 
However, this comes at the cost of adjusted BOTS.ini and job2queue.py which are not as per BOTS source. 


### Azure Service Bus 
A continous WebJob 'azurequeue' receives messages and stores them in BOTSSYS/botsqueue directory.
The messages are expected in following format:

JSON Format:

    {'route': 'azurequeue',
    'filename': '6820162_20140611201926_1009634015.txt',
    'content': base64gzip-encoded-content
    }

The content must be base64 encoded and gzipped.
example:
file = open("some_edi_file.txt")
base64gz = base64.b64encode(zlib.compress(file.read()))

The files are written into the directory BOTSSYS/botsqueue.
The routes should have this directory as income channel only.
The route MUST delete the file.


## Deploy
 
[![Deploy to Azure](http://azuredeploy.net/deploybutton.png)](https://azuredeploy.net/)

The project does not yet contain an azuredeploy.json -> that might follow.