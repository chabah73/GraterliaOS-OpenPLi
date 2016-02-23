from Components.Language import language
from Tools.Directories import pathExists, resolveFilename, SCOPE_GOSLANGUAGE, SCOPE_PLUGINS
import os,gettext
LanguageDomains = []

def localeInit():
    global LanguageDomains
    lang = language.getLanguage()[:2]
    os.environ["LANGUAGE"] = lang
    for file in os.listdir(resolveFilename(SCOPE_GOSLANGUAGE, "%s/LC_MESSAGES/") % str(lang)):
        myDomain = file[:-3]
        if file.startswith("plugin-") and file.endswith(".mo"):
            if pathExists(resolveFilename(SCOPE_PLUGINS, "Extensions/%s" % myDomain[7:])) or pathExists(resolveFilename(SCOPE_PLUGINS, "SystemPlugins/%s" % myDomain[7:])):
                print "[GOSlocale] binding %s as '%s' domain" % (file , myDomain)
                gettext.bindtextdomain(myDomain, resolveFilename(SCOPE_GOSLANGUAGE))
                LanguageDomains.append(myDomain)

def gosgettext(txt, myDomain = 'auto'):
    t = ''
    if myDomain == 'auto':
        print "[GOSlocale] AutoDomains '%s'" % txt
        for tempDomain in LanguageDomains:
            #print "AutoDomains, current: '%s'" % tempDomain
            t = gettext.dgettext(tempDomain, txt)
            if t != txt:
                #print "Autotranslated '%s' to '%s'" % (txt,t)
                return t
    elif myDomain == 'enigma2':
        t = gettext.gettext(txt)
        return t
    else:
        #print "[GOSlocale] Selected myDomain '%s' '%s'" % (myDomain , txt)
        t = gettext.dgettext(myDomain, txt)
    
    if t == txt or t == '':
        #print "[GOSlocale] fallback to default translation for '%s'" % txt
        t = gettext.gettext(txt)
    return t

localeInit()
language.addCallback(localeInit)
