# From:
# https://code.google.com/p/android-scripting/wiki/FullScreenUI
import android
try:
    # Create droid object if we're on the phone
    droid = android.Android()
except:
    try:
        # Create droid object if we're on computer
        droid=android.Android(('192.168.3.10','36161'))
    except:
        raise RuntimeError("Could not connect to android device")

from urllib2 import urlopen
import json

from model import Buff, Attack, DamageRoll
attacks = [Attack('Tidewater Cutless +1 (MH)',8,DamageRoll(1,6,5),[18,19,20],2),
           Attack('Masterwork Handaxe (OH)',8,DamageRoll(1,6,4),[20,],3)]
#buffs = [Buff('Favored Enemy (Human)',4,4),
#         Buff('Favored Enemy (Monstrous Humanoid)',2,2),
#         Buff('100 to damage',dmg_mod=95)]

def readOnlineBuffs():
    r = urlopen(r"http://genericlifeform.pythonanywhere.com/IBC/api/v1.0/buffs")
    buffs_json = json.load(r)['buffs']
    buffs = []
    for b in buffs_json:
        buffs.append(Buff.fromDict(b))
    return buffs
buffs = readOnlineBuffs()


def eventloop():
    global buffs, attacks
    while True:
        event=droid.eventWait().result
        print event
        if event["name"]=="click":
            id=event["data"]["id"]
            if id[:4] == "Buff":
                # A buff has been updated
                active_buffs = []
                for n, b in enumerate(buffs):
                    info = get_info = droid.fullQueryDetail("Buff%d"%n).result
                    if info['checked']=='true':
                        active_buffs.append(b)
                print "Active Buffs:", active_buffs
                for a in attacks:
                    a.updateUI(active_buffs, droid)
            elif id[:10] == "RollBtnAtk":
                # User asked for us to roll an attack
                atk_id = int(id[10:])
                atk = attacks[atk_id]
                alert_dialog(atk.name, atk.roll())
        elif event['name']=='menu_newBuff':
            #droid.fullDismiss()
            with open("newBuff.xml") as f:
                layout2 = f.read()
            print droid.fullShow(layout2)
            buffs = eventloop_newBuff()
            buildMainWindow(attacks, buffs)
        elif event['name']=='menu_quit':
            # Quit menu bar button
            return
        elif event["name"]=="screen":
            if event["data"]=="destroy":
                return

def eventloop_newBuff():
    global buffs
    while True:
        event=droid.eventWait().result
        print "In newBuff:", event
        if event["name"]=="click":
            id=event["data"]["id"]
            if id == "btnSave":
                # A buff has been updated
                name = droid.fullQueryDetail("buffName").result['text']
                atk = droid.fullQueryDetail("buffAtk").result['text']
                dmg = droid.fullQueryDetail("buffDmg").result['text']
                print name, atk, dmg
                buffs += [Buff(name, atk, dmg)]
                break
            elif id[:10] == "btnCancel":
                # User cancels, return
                break
        elif event['name']=='menu_quit':
            # Quit menu bar button
            break
        elif event["name"]=="screen":
            if event["data"]=="destroy":
                break
    return buffs


def alert_dialog(title, message, buttonText='Ok'):
  droid.dialogCreateAlert(title, message)
  droid.dialogSetPositiveButtonText('Continue')
  droid.dialogShow()
  response = droid.dialogGetResponse().result
  return response['which'] == 'positive'


def buildMainWindow(attacks, buffs):
    with open("main_window.xml") as f:
        layout_template = f.read()
    atk_xml = '\n\n'.join([x.makeUI(n) for n,x in enumerate(attacks)])
    buffs_xml = '\n\n'.join([x.makeUI(n) for n,x in enumerate(buffs)])

    layout = layout_template % {'Buffs':buffs_xml, 'Attacks':atk_xml}
    print layout

    ###################################################################
    # See: http://www.mithril.com.au/android/doc/UiFacade.html#addOptionsMenuItem
    # Icons: http://androiddrawableexplorer.appspot.com/
    droid.clearOptionsMenu()
    droid.addOptionsMenuItem("Silly","silly",None,"star_on")
    droid.addOptionsMenuItem("New Buff","menu_newBuff",None,"star_off")
    droid.addOptionsMenuItem("Quit","menu_quit",None,"btn_close_normal")

    print droid.fullShow(layout)

buildMainWindow(attacks, buffs)
eventloop()
print droid.fullQuery()
print "Data entered =",droid.fullQueryDetail("editText1").result
droid.fullDismiss()