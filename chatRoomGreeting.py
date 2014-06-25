import logging
from errbot import BotPlugin, PY3, botcmd
from errbot.version import VERSION
from errbot.holder import bot

__author__ = 'apophys'
from config import CHATROOM_PRESENCE, CHATROOM_FN

# 2to3 hack
# thanks to https://github.com/oxplot/fysom/issues/1
# which in turn references http://www.rfk.id.au/blog/entry/preparing-pyenchant-for-python-3/
if PY3:
    basestring = (str, bytes)


class ChatRoomGreeting(BotPlugin):
    min_err_version = VERSION  # don't copy paste that for your plugin, it is just because it is a bundled plugin !
    max_err_version = VERSION

    got_entire_roster = set()

    def activate(self):
        super(ChatRoomGreeting, self).activate()
       #  if bot.mode == 'xmpp':
       #      for room in self.get('rooms_enabled', set()):
       #          bot.conn.add_event_handler('muc::%s::got_online' % room,
       #                                     self.callback_muc_presence)

    def deactivate(self):
        # for room in CHATROOM_PRESENCE:
        #     bot.conn.del_event_handler('muc::%s::got_online' % room,
        #                                self.callback_muc_presence)
        self.active = False
        super(ChatRoomGreeting, self).deactivate()

    # def callback_muc_presence(self, pres):
    def callback_user_joined_chat(self, conn, pres):
        if bot.mode == 'xmpp':
            # check for the status of the room roster
            room = pres['from'].node
            nick = pres['from'].resource
            logging.debug("Presence for nick {} room {}.".format(nick, room))
            if room in self.got_entire_roster:
                if pres['from'] in self.get('disabled_nicks', set()):
                    return

                msg = "Hello, %s!" % (pres['from'].resource,)
                to = pres['from'].bare
                self.send(to, msg, message_type='groupchat')
            else:
                if nick == CHATROOM_FN:
                    logging.debug("Got entire roster in initial MUC presence "
                                 " broadcast for room {}.".format(room))
                    self.got_entire_roster.add(room)
                    return
                else:
                    logging.debug("Ignoring initial presence.")
                    return

    @botcmd
    def greeting_stop(self, mess, _):
        """Stops sending messages to the user."""

        if bot.mode == 'xmpp':
            nick = mess.getFrom().resource
            disable_nick = str(mess.getFrom())
            try:
                nicks = self.get('disabled_nicks', set())
                nicks.add(disable_nick)
                self['disabled_nicks'] = nicks
            except Exception as _:
                return "An error occured. Try again."

            return "Greeting disabled for user {}".format(nick)

    @botcmd
    def greeting_start(self, mess, _):
        """Enables sending of the messages to the user."""
        
        if bot.mode == 'xmpp':
            nick = mess.getFrom().resource
            enable_nick = str(mess.getFrom())
            try:
                nicks = self.get('disabled_nicks', set())
                nicks.discard(enable_nick)
                self['disabled_nicks'] = nicks
            except Exception as _:
                return "An error occured. Try again."
            return "Nick {} will receive greeting messages again.".format(nick)

    @botcmd(admin_only=True, split_args_with=' ')
    def greeting_enable(self, mess, args):
        # FIXME
        message = "This command is not usable at the moment."
        return message

        ###################
        # TODO: remove this
        if len(args) > 1:
            message = ("You can't allow multiple rooms in one call at the moment."
                       "Configuring only the first.")

        room_to_enable = args[0]
        try:
            rooms = self.get('rooms_enabled', set())
            rooms.add(room_to_enable)
            self['rooms_enabled'] = rooms
            bot.conn.add_event_handler('muc::%s::got_online' % room_to_enable,
                                       self.callback_muc_presence)
            message = "Room {} enabled.".format(room_to_enable)
        except Exception as _:
            message = "Configuring the plugin for room {0} failed.".format(room_to_enable)

        return message

    @botcmd(admin_only=True, split_args_with=' ')
    def greeting_disable(self, mess, args):
        # FIXME
        message = "This command is not usable at the moment."
        return message
        
        ##################
        message = ""
        if len(args) > 1:
            message = "You can't allow multiple rooms in one call at the moment." \
                      "Configuring only the first."

        room_to_disable = args[0]

        try:
            rooms = self.get('rooms_enabled', set())
            rooms.discard(room_to_disable)

            self['rooms_enabled'] = rooms
            bot.conn.del_event_handler('muc::%s::got_online' % room_to_disable,
                                       self.callback_muc_presence)
            message = "Room {} disabled.".format(room_to_disable)
        except Exception as _:
            message = "Configuring the plugin for room {0} failed.".format(
                      room_to_disable)

        return message

    @botcmd(admin_only=True)
    def greeting_reset(self, mess, args):
        self['disabled_nicks'] = set()

        return "All nicks excluded from greeting were purged."

    @botcmd(admin_only=True)
    def greeting_list(self, mess, args):
        message = "List of users excluded from greeting:\n{}"

        nicks = ('\n'.join(self.get('disabled_nicks', '')) or
                 "There are no usernames excluded from the greeting.")

        return message.format(nicks)
