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

from urllib2 import urlopen, Request
import json

from model import Buff, Attack, DamageRoll, Character, Weapon
########
# BUILD HENRI
#######
c = Character()
c.base.str_score = 19
c.base.dex_score = 12
c.base.con_score = 13
c.base.cha_score = 14

c.BAB = 5

greatsword = Weapon("Greatsword",
                      Attack(atk=+0, dmg_roll=DamageRoll.fromString("2d6"),
                             crit_range=[19,20], crit_mult=2, two_handed=True))
c.equipment.main_hand = greatsword
attacks = c.attacks


#attacks = [Attack(9,DamageRoll(1,6,5),[18,19,20],2,name='Tidewater Cutless (MH_1)'),
#           Attack(4,DamageRoll(1,6,5),[18,19,20],2,name='Tidewater Cutless (MH_2)'),
#           Attack(9,DamageRoll(1,6,4),[20,],3,name='Masterwork Handaxe (OH_1)'),
#           Attack(4,DamageRoll(1,6,4),[20,],3,name='Masterwork Handaxe (OH_2)'),
#           Attack(10,DamageRoll(1,8,4),[20,],3,name='Battleaxe (StdAct#1)'),
#           Attack(5,DamageRoll(1,8,4),[20,],3,name='Battleaxe (StdAct#2)'),
#           Attack(4,DamageRoll(1,8,5),[20,],3,name='Vindictive Harpoon +1 (Rng)'),]


def readOnlineBuffs():
    r = urlopen(r"http://genericlifeform.pythonanywhere.com/IBC/api/v1.0/buffs")
    buffs_json = json.load(r)['buffs']
    buffs = []
    for b in buffs_json:
        buffs.append(Buff.fromDict(b))
    return buffs
try:
    buffs = readOnlineBuffs()
except:
    droid.makeToast("Unable to communicate with server")
    buffs = [Buff('Favored Enemy (Human)',4,4),
             Buff('Favored Enemy (Monstrous Humanoid)',2,2),
             Buff('Bless',atk_mod=1),
             Buff('Prayer',atk_mod=1,dmg_mod=1),
             Buff('Sickened',atk_mod=-2,dmg_mod=-2)]


def eventloop():
    global buffs, attacks
    while True:
        event=droid.eventWait().result
        print event
        if event["name"]=="click":
            id=event["data"]["id"]
            if id[:4] == "Buff":
                # A buff has been updated
                c.buffs = []        # TODO: Make character buff list instead
                for n, b in enumerate(buffs):
                    info = get_info = droid.fullQueryDetail("Buff%d"%n).result
                    if info['checked']=='true':
                        c.buffs.append(b)
                print "Active Buffs:", c.buffs
                for a in attacks:
                    a.updateUI(c.buffs, droid)
            elif id[:10] == "RollBtnAtk":
                # User asked for us to roll an attack
                atk_id = int(id[10:])
                atk = attacks[atk_id]
                alert_dialog(atk.name, atk.roll())
        elif event['name']=='menu_newBuff':
            #droid.fullDismiss()
            buildPopup("newBuff.xml",attacks, buffs)
            buffs = eventloop_newBuff()
            buildMainWindow(attacks, buffs)
        elif event['name']=='menu_delBuff':
            # Delete a buff
              droid.dialogCreateAlert("Delete Buff")
              droid.dialogSetSingleChoiceItems(
                    map(lambda x: x.name, buffs))
              droid.dialogSetPositiveButtonText("Ok")
              droid.dialogSetNegativeButtonText("Cancel")
              droid.dialogShow()
              response = droid.dialogGetResponse().result
              if response['which'] == 'positive':
                idx = droid.dialogGetSelectedItems().result[0]
                print "deleting %d" % idx
                buff = buffs.pop(idx)
                buildPost(buff.makeDict(), mode='delete')
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
                new_buff =Buff(name, atk, dmg)
                buffs += [new_buff]
                # Post it to the webserver
                buildPost(new_buff.makeDict())
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
        elif event['name']=='key':
            if event['data']['key'] == '4':
                # Back button pushed.  Do same as cancel
                break
    return buffs

def buildPost(d, mode='add'):
    """Create a JSON paylod of dictionary and post"""
    url=r"http://genericlifeform.pythonanywhere.com/IBC/api/v1.0/buffs"
    s = "Unable to post new buff to website"
    if mode == 'delete':
        url += r"/del/%d" % d['id']

    try:
        payload = json.dumps(d)
        header = {'Content-Type': 'application/json'}
        req = Request(url, payload, header)
        response = urlopen(req)
        if response.getcode() == 201:
            return
    except Exception, e:
        s += '\nERROR: ' + str(e)
    alert_dialog("Posting Error", s, "Ok")

def alert_dialog(title, message, buttonText='Continue'):
  droid.dialogCreateAlert(title, message)
  droid.dialogSetPositiveButtonText(buttonText)
  droid.dialogShow()
  response = droid.dialogGetResponse().result
  return response['which'] == 'positive'

xml_header = '<?xml version="1.0" encoding="utf-8"?>'
def buildMainWindow(attacks, buffs, returnString=False):
    with open("layouts\main_window.xml") as f:
        layout_template = f.read()
    atk_xml = '\n\n'.join([x.makeUI(n) for n,x in enumerate(attacks)])
    buffs_xml = '\n\n'.join([x.makeUI(n) for n,x in enumerate(buffs)])

    layout = layout_template % {'Buffs':buffs_xml, 'Attacks':atk_xml}

    ###################################################################
    # See: http://www.mithril.com.au/android/doc/UiFacade.html#addOptionsMenuItem
    # Icons: http://androiddrawableexplorer.appspot.com/
    droid.clearOptionsMenu()
    droid.addOptionsMenuItem("Silly","silly",None,"star_on")
    droid.addOptionsMenuItem("New Buff","menu_newBuff",None,"star_off")
    droid.addOptionsMenuItem("Delete Buff","menu_delBuff",None,"ic_menu_delete")
    droid.addOptionsMenuItem("Quit","menu_quit",None,"btn_close_normal")

    droid.addContextMenuItem("Test", "cm_test",None)

    if returnString:
        return layout
    else:
        print droid.fullShow(xml_header+layout)

def buildPopup(popup_xml, attacks, buffs):
    with open("layouts\popup.xml") as f:
        base = f.read()
    with open("layouts\\"+popup_xml) as f:
        popup = f.read()
    main_window = buildMainWindow(attacks, buffs, True)
    base = xml_header+base
    print droid.fullShow(base % locals())

buildMainWindow(attacks, buffs)
eventloop()
print droid.fullQuery()
print "Data entered =",droid.fullQueryDetail("editText1").result
droid.fullDismiss()