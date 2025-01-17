#! /usr/bin/env python

"""
   Program:   EQ Alert
   File Name: eqa/lib/parser.py
   Copyright (C) 2022 Michael Geitz

   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 2 of the License, or
   (at your option) any later version.
   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.
   You should have received a copy of the GNU General Public License along
   with this program; if not, write to the Free Software Foundation, Inc.,
   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

from collections import deque
import sys
import time
import re

import eqa.lib.struct as eqa_struct
import eqa.lib.settings as eqa_settings


def process(exit_flag, log_q, action_q):
    """
    Process: log_q
    Produce: action_q
    """

    try:
        while not exit_flag.is_set():
            time.sleep(0.001)
            if not log_q.empty():
                # Read raw log line
                log_line = log_q.get()
                log_q.task_done()
                # Strip line of any trailing space
                line = log_line.strip()
                if (
                    re.fullmatch(
                        r"^\[(?:Fri|Mon|S(?:at|un)|T(?:hu|ue)|Wed) (?:A(?:pr|ug)|Dec|Feb|J(?:an|u[ln])|Ma[ry]|Nov|Oct|Sep) [0-9]{2} [0-9]{2}\:[0-9]{2}\:[0-9]{2} [0-9]{4}\] .+",
                        line,
                    )
                    is not None
                ):
                    # Split timestamp and message payload
                    timestamp, payload = line[1:].split("] ", 1)
                    timestamp = timestamp.split(" ")[3] + ".00"
                    # Determine line type
                    line_type = determine(payload)
                    # Build and queue action
                    new_message = eqa_struct.message(
                        timestamp, line_type, "null", "null", payload
                    )
                    action_q.put(new_message)
                else:
                    eqa_settings.log("process_log: Cannot process: " + line)

    except Exception as e:
        eqa_settings.log(
            "process_log: Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def determine(line):
    """Determine type of line"""

    try:
        # Melee
        line_type = check_melee(line)
        if line_type is not None:
            return line_type

        # Spell
        line_type = check_spell(line)
        if line_type is not None:
            return line_type

        # Received Player Chat
        line_type = check_received_chat(line)
        if line_type is not None:
            return line_type

        # Sent Player Chat
        line_type = check_sent_chat(line)
        if line_type is not None:
            return line_type

        # Command Output
        line_type = check_command_output(line)
        if line_type is not None:
            return line_type

        # System Messages
        line_type = check_system_messages(line)
        if line_type is not None:
            return line_type

        # Group System Messages
        line_type = check_group_system_messages(line)
        if line_type is not None:
            return line_type

        # Loot Trade Messages
        line_type = check_loot_trade(line)
        if line_type is not None:
            return line_type

        # Emotes
        line_type = check_emotes(line)
        if line_type is not None:
            return line_type

        # Who
        line_type = check_who(line)
        if line_type is not None:
            return line_type

        # Pets
        line_type = check_pets(line)
        if line_type is not None:
            return line_type

        # No Match Found
        return "undetermined"

    except Exception as e:
        eqa_settings.log(
            "process_log (determine): Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )

    return line_type


def check_melee(line):
    """
    Check line for melee
    """
    try:
        # Melee Combat
        if (
            re.fullmatch(
                r"^[a-zA-Z\s]+ (hits|crushes|slashes|pierces|bashes|backstabs|bites|kicks|claws|gores|punches|strikes|slices) [a-zA-Z\s]+ for \d+ points of damage\.",
                line,
            )
            is not None
        ):
            return "combat_other_melee"
        elif (
            re.fullmatch(
                r"^[a-zA-Z\s]+ tries to (hit|crush|slash|pierce|bash|backstab|bite|kick|claw|gore|punch|strike|slice) [a-zA-Z\s]+, but misses\!",
                line,
            )
            is not None
        ):
            return "combat_other_melee_miss"
        elif (
            re.fullmatch(
                r"^[a-zA-Z\s]+ tries to (hit|crush|slash|pierce|bash|backstab|bite|kick|claw|gore|punch|strike|slice) [a-zA-Z\s]+, but [a-zA-Z\s]+ dodges\!",
                line,
            )
            is not None
        ):
            return "combat_other_melee_dodge"
        elif (
            re.fullmatch(
                r"^[a-zA-Z\s]+ tries to (hit|crush|slash|pierce|bash|backstab|bite|kick|claw|gore|punch|strike|slice) [a-zA-Z\s]+, but [a-zA-Z\s]+ parries\!",
                line,
            )
            is not None
        ):
            return "combat_other_melee_parry"
        elif (
            re.fullmatch(
                r"^[a-zA-Z\s]+ tries to (hit|crush|slash|pierce|bash|backstab|bite|kick|claw|gore|punch|strike|slice) [a-zA-Z\s]+, but [a-zA-Z\s]+ blocks\!",
                line,
            )
            is not None
        ):
            return "combat_other_melee_block"
        elif (
            re.fullmatch(
                r"^[a-zA-Z\s]+ tries to (hit|crush|slash|pierce|bash|backstab|bite|kick|claw|gore|punch|strike|slice) [a-zA-Z\s]+, but [a-zA-Z\s]+ ripostes\!",
                line,
            )
            is not None
        ):
            return "combat_other_melee_reposte"
        elif (
            re.fullmatch(
                r"^[a-zA-Z\s]+ (hits|crushes|slashes|pierces|bashes|backstabs|bites|kicks|claws|gores|punches|strikes|slices) you for \d+ points of damage\.",
                line,
            )
            is not None
        ):
            return "combat_you_receive_melee"
        elif (
            re.fullmatch(
                r"^You (hit|crush|slash|pierce|bash|backstab|bite|kick|claw|gore|punch|strike|slice) [a-zA-Z\s]+ for \d+ points of damage\.",
                line,
            )
            is not None
        ):
            return "combat_you_melee"
        elif (
            re.fullmatch(
                r"^You try to (hit|crush|slash|pierce|bash|backstab|bite|kick|claw|gore|punch|strike|slice) [a-zA-Z\s]+, but miss\!",
                line,
            )
            is not None
        ):
            return "combat_you_melee_miss"
        elif (
            re.fullmatch(r"^[a-zA-Z\s]+ Scores a critical hit\!\(\d+\)$", line)
            is not None
        ):
            return "combat_other_melee_crit"
        elif (
            re.fullmatch(r"^[a-zA-Z\s]+ has become (ENRAGED|enraged)\.$", line)
            is not None
        ):
            return "mob_enrage_on"
        elif re.fullmatch(r"^[a-zA-Z\s]+ is no longer enraged\.$", line) is not None:
            return "mob_enrage_off"
        elif (
            re.fullmatch(r"^[a-zA-Z\s]+ goes on a (RAMPAGE|rampage)\.$", line)
            is not None
        ):
            return "mob_rampage_on"
        elif (
            re.fullmatch(r"^[a-zA-Z\s]+ has been slain by [a-zA-Z\s]+\!$", line)
            is not None
        ):
            return "mob_slain_other"
        elif re.fullmatch(r"^You have slain [a-zA-Z\s]+\!$", line) is not None:
            return "mob_slain_you"
        elif (
            re.fullmatch(r"^Your target is out of range, get closer\!$", line)
            is not None
        ):
            return "mob_out_of_range"
        elif re.fullmatch(r"^You gain experience\!\!$", line) is not None:
            return "experience_solo"
        elif re.fullmatch(r"^You gain party experience\!\!$", line) is not None:
            return "experience_group"
        elif re.fullmatch(r"^You are stunned\!$", line) is not None:
            return "combat_you_stun_on"
        elif re.fullmatch(r"^You are unstunned\.$", line) is not None:
            return "combat_you_stun_off"

        return None

    except Exception as e:
        eqa_settings.log(
            "process_log (check_melee): Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def check_spell(line):
    """
    Check line for spell
    """
    try:
        if re.fullmatch(r"^[a-zA-Z\s]+ begins to cast a spell\.$", line) is not None:
            return "spell_cast_other"
        elif re.fullmatch(r"^You begin casting [a-zA-Z\s]+\.$", line) is not None:
            return "spell_cast_you"
        elif re.fullmatch(r"^\w+\'s spell fizzles\!$", line) is not None:
            return "spell_fizzle_other"
        elif re.fullmatch(r"^Your spell fizzles\!$", line) is not None:
            return "spell_fizzle_you"
        elif re.fullmatch(r"^Your spell did not take hold\.$", line) is not None:
            return "spell_not_hold"
        elif (
            re.fullmatch(r"^Insufficient Mana to cast this spell\!$", line) is not None
        ):
            return "spell_cast_oom"
        elif (
            re.fullmatch(r"^[a-zA-Z\s]+\'s casting is interrupted\!$", line) is not None
        ):
            return "spell_interrupt_other"
        elif re.fullmatch(r"^Your spell is interrupted\.$", line) is not None:
            return "spell_interrupt_you"
        elif (
            re.fullmatch(
                r"^[a-zA-Z\s]+ regains concentration and continues casting\.$", line
            )
            is not None
        ):
            return "spell_recover_other"
        elif (
            re.fullmatch(
                r"^You regain your concentration and continue your casting\.$", line
            )
            is not None
        ):
            return "spell_recover_you"
        elif re.fullmatch(r"^Your target resisted the .+ spell\.$", line) is not None:
            return "spell_resist_you"
        elif (
            re.fullmatch(
                r"^.+ w(?:ere|as) hit by non-melee for \d+ ?(points of) damage\.$", line
            )
            is not None
        ):
            return "spell_damage"
        elif (
            re.fullmatch(r"^Beginning to memorize [a-zA-Z\s\'\:]+\.\.\.$", line)
            is not None
        ):
            return "spell_memorize_begin"
        elif (
            re.fullmatch(r"^You have finished memorizing [a-zA-Z\s\'\:]+\.$", line)
            is not None
        ):
            return "spell_memorize_finish"
        elif (
            re.fullmatch(
                r"^$You cannot memorize a spell you already have memorized\.", line
            )
            is not None
        ):
            return "spell_memorize_already"
        elif re.fullmatch(r"^You forget .+\.", line) is not None:
            return "spell_forget"
        elif re.fullmatch(r"^\w+ begins to regenerate\.$", line) is not None:
            return "spell_regen_on"
        elif re.fullmatch(r"^Your [a-zA-Z\s]+ spell has worn off\.$", line) is not None:
            return "spell_worn_off"
        elif (
            re.fullmatch(r"^You have healed .+ for \d+ points of damage\.$", line)
            is not None
        ):
            return "spell_heal_you"
        elif re.fullmatch(r"^Your target has been cured\.$", line) is not None:
            return "spell_cured"
        elif (
            re.fullmatch(r"^Your gate is too unstable, and collapses\.$", line)
            is not None
        ):
            return "spell_gate_collapse"
        elif re.fullmatch(r"^You haven't recovered yet\.\.\.$", line) is not None:
            return "spell_cooldown_active"

        return None

    except Exception as e:
        eqa_settings.log(
            "process_log (check_spell): Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def check_received_chat(line):
    """
    Check line for received chat
    """

    try:
        if re.fullmatch(r"^\w+ tells you, \'.+\'$", line) is not None:
            return "tell"
        elif re.fullmatch(r"^\w+ says, \'.+\'$", line) is not None:
            return "say"
        elif re.fullmatch(r"^\w+ shouts, \'.+\'$", line) is not None:
            return "shout"
        elif re.fullmatch(r"^\w+ tells the guild, \'.+\'$", line) is not None:
            return "guild"
        elif re.fullmatch(r"^\w+ tells the group, \'.+\'$", line) is not None:
            return "group"
        elif re.fullmatch(r"^\w+ says out of character, \'.+\'$", line) is not None:
            return "ooc"
        elif (
            re.fullmatch(r"^\w+ auctions, \'(.+|)(WTS|selling|Selling)(.+|)\'$", line)
            is not None
        ):
            return "auction_wts"
        elif (
            re.fullmatch(r"^\w+ auctions, \'(.+|)(WTB|buying|Buying)(.+|)\'$", line)
            is not None
        ):
            return "auction_wtb"
        elif re.fullmatch(r"^\w+ auctions, \'.+\'$", line) is not None:
            return "auction"

        return None

    except Exception as e:
        eqa_settings.log(
            "process_log (check_received_chat): Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def check_sent_chat(line):
    """
    Check line for sent chat
    """

    try:
        if re.fullmatch(r"^You told \w+(, \'| \'\[queued\],).+\'$", line) is not None:
            return "you_tell"
        elif re.fullmatch(r"^You say, \'.+\'$", line) is not None:
            return "you_say"
        elif re.fullmatch(r"^You shout, \'.+\'$", line) is not None:
            return "you_shout"
        elif re.fullmatch(r"^You say to your guild, \'.+\'$", line) is not None:
            return "you_guild"
        elif re.fullmatch(r"^You tell your party, \'.+\'$", line) is not None:
            return "you_group"
        elif re.fullmatch(r"^You say out of character, \'.+\'$", line) is not None:
            return "you_ooc"
        elif re.fullmatch(r"^You auction, \'.+\'$", line) is not None:
            return "you_auction"

        return None

    except Exception as e:
        eqa_settings.log(
            "process_log (check_sent_chat): Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def check_command_output(line):
    """
    Check line for command output
    """

    try:
        if (
            re.fullmatch(
                r"^Your Location is [-]?(?:\d*\.)?\d+\,\ [-]?(?:\d*\.)?\d+\,\ [-]?(?:\d*\.)?\d+$",
                line,
            )
            is not None
        ):
            return "location"
        elif (
            re.fullmatch(
                r"^You think you are heading (?:North(?:East|West)?|South(?:East|West)?|(?:Ea|We)st)\.$",
                line,
            )
            is not None
        ):
            return "direction"
        elif (
            re.fullmatch(r"^You have no idea what direction you are facing\.$", line)
            is not None
        ):
            return "direction_miss"
        elif (
            re.fullmatch(r"^You are now A\.F\.K\. \(Away From Keyboard\)\.", line)
            is not None
        ):
            return "you_afk_on"
        elif re.fullmatch(r"^You are now Looking For a Group\.", line) is not None:
            return "you_lfg_on"
        elif (
            re.fullmatch(r"^You are no longer A\.F\.K\. \(Away From Keyboard\)\.", line)
            is not None
        ):
            return "you_afk_off"
        elif (
            re.fullmatch(r"^You are no longer Looking For a Group\.", line) is not None
        ):
            return "you_lfg_off"
        elif (
            re.fullmatch(
                r"^It will take (you |)about (30|25|20|15|10|5) (more |)seconds to prepare your camp\.$",
                line,
            )
            is not None
        ):
            return "you_camping"
        elif (
            re.fullmatch(r"^You abandon your preparations to camp\.$", line) is not None
        ):
            return "you_camping_abandoned"
        elif re.fullmatch(r"^\*\*.+", line) is not None:
            return "random"
        elif re.fullmatch(r"^Game Time\:.+", line) is not None:
            return "time_game"
        elif re.fullmatch(r"^Earth Time\:.+", line) is not None:
            return "time_earth"
        elif re.fullmatch(r"^MESSAGE OF THE DAY\:.+", line) is not None:
            return "motd_game"
        elif re.fullmatch(r"^GUILD MOTD\:.+", line) is not None:
            return "motd_guild"
        elif (
            re.fullmatch(r"^You can\'t use that command while casting\.\.\.$", line)
            is not None
        ):
            return "command_block"

        return None

    except Exception as e:
        eqa_settings.log(
            "process_log (check_command_output): Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def check_system_messages(line):
    """
    Check line for system messages
    """

    try:
        if re.fullmatch(r"^You have entered [a-zA-Z\s\'\:]+\.$", line) is not None:
            return "you_new_zone"
        elif re.fullmatch(r"^LOADING, PLEASE WAIT\.\.\.$", line) is not None:
            return "zoning"
        elif re.fullmatch(r"^You are out of food\.", line) is not None:
            return "you_outfood"
        elif re.fullmatch(r"^You are out of drink\.", line) is not None:
            return "you_outdrink"
        elif re.fullmatch(r"^You are out of food and drink\.", line) is not None:
            return "you_outfooddrink"
        elif re.fullmatch(r"^You are out of food and low on drink\.", line) is not None:
            return "you_outfoodlowdrink"
        elif re.fullmatch(r"^You are out of drink and low on food\.", line) is not None:
            return "you_outdrinklowfood"
        elif re.fullmatch(r"^You are thirsty\.", line) is not None:
            return "you_thirsty"
        elif re.fullmatch(r"^You are hungry\.", line) is not None:
            return "you_hungry"
        elif re.fullmatch(r"^You are no longer encumbered\.$", line) is not None:
            return "encumbered_off"
        elif re.fullmatch(r"^You are encumbered\!$", line) is not None:
            return "encumbered_on"
        elif (
            re.fullmatch(r"^You have become better at [a-zA-Z\s]+\! \(\d+\)$", line)
            is not None
        ):
            return "skill_up"
        elif re.fullmatch(r"^Welcome to level \d+\!", line) is not None:
            return "ding_up"
        elif (
            re.fullmatch(r"^You LOST a level\! You are now level \d+\!", line)
            is not None
        ):
            return "ding_down"
        elif re.fullmatch(r"^It begins to rain\.$", line) is not None:
            return "weather_start_rain"
        elif re.fullmatch(r"^It begins to snow\.$", line) is not None:
            return "weather_start_snow"
        elif re.fullmatch(r"^You can\'t reach that, get closer\.$", line) is not None:
            return "you_cannot_reach"
        elif (
            re.fullmatch(
                r"^Your faction standing with \w+ (?:could not possibly get any|got) (?:better|worse)\.$",
                line,
            )
            is not None
        ):
            return "faction_line"
        elif re.fullmatch(r"^[a-zA-Z\s]+ engages \w+\!$", line) is not None:
            return "engage"
        elif (
            re.fullmatch(
                r"^(Targeted \((NPC|Player)\)\: [a-zA-Z\s]+|You no longer have a target\.)",
                line,
            )
            is not None
        ):
            return "target"
        elif re.fullmatch(r"^Welcome to EverQuest\!$", line) is not None:
            return "motd_welcome"
        elif (
            re.fullmatch(
                r"^[a-zA-Z\s]+ is (?:behind and to the (?:righ|lef)t\.|ahead and to the (?:righ|lef)t\.|(?:straight ahead|behind you)\.|to the (?:righ|lef)t\.)$",
                line,
            )
            is not None
        ):
            return "tracking"

        return None

    except Exception as e:
        eqa_settings.log(
            "process_log (check_system_messages): Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def check_group_system_messages(line):
    """
    Check line for group system messages
    """

    try:
        if re.fullmatch(r"^[a-zA-Z]+ has gone Linkdead.", line) is not None:
            return "player_linkdead"
        elif re.fullmatch(r"^You have joined the group\.", line) is not None:
            return "group_joined"
        elif re.fullmatch(r"^\w+ has joined the group\.$", line) is not None:
            return "group_joined_other"
        elif re.fullmatch(r"^\w+ has left the group\.$", line) is not None:
            return "group_leave_other"
        elif re.fullmatch(r"^You have been removed from the group\.", line) is not None:
            return "group_removed"
        elif (
            re.fullmatch(r"^You invite [a-zA-Z]+ to join your group\.$", line)
            is not None
        ):
            return "group_invite_other"
        elif (
            re.fullmatch(r"^[a-zA-Z]+ invites you to join a group\.$", line) is not None
        ):
            return "group_invite_you"
        elif (
            re.fullmatch(
                r"^To join the group, click on the \'FOLLOW\' option, or \'DISBAND\' to cancel\.$",
                line,
            )
            is not None
        ):
            return "group_invite_instruction"
        elif re.fullmatch(r"^Your group has been disbanded\.$", line) is not None:
            return "group_disbanded"
        elif (
            re.fullmatch(
                r"^You notify [a-zA-Z]+ that you agree to join the group\.$", line
            )
            is not None
        ):
            return "group_join_notify"

        return None

    except Exception as e:
        eqa_settings.log(
            "process_log (check_group_system_messages): Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def check_loot_trade(line):
    """
    Check line for looting or trading
    """

    try:
        if re.fullmatch(r"^\-\-\w+ has looted [a-zA-Z\s\:]+\.\-\-$", line) is not None:
            return "looted_item_other"
        elif (
            re.fullmatch(r"^\-\-You have looted [a-zA-Z\s\:]+\.\-\-$", line) is not None
        ):
            return "looted_item_you"
        elif (
            re.fullmatch(
                r"^You receive (\d+ platinum, |)(\d+ gold, |)(\d+ silver and |)\d+ copper from the corpse\.$",
                line,
            )
            is not None
        ):
            return "looted_money_you"
        elif (
            re.fullmatch(
                r"^You receive \d+ platinum, \d+ gold, \d+ silver, \d+ copper as your split\.$",
                line,
            )
            is not None
        ):
            return "looted_money_other"
        elif (
            re.fullmatch(r"^The total trade is\: \d+ PP, \d+ GP, \d+ SP, \d+ CP$", line)
            is not None
        ):
            return "trade_money"
        elif (
            re.fullmatch(r"^[a-zA-Z]+ has offered you [a-zA-Z\s]+\.$", line) is not None
        ):
            return "trade_item"

        return None

    except Exception as e:
        eqa_settings.log(
            "process_log (check_loot_trade): Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def check_emotes(line):
    """
    Check line for emotes
    """

    try:
        if re.fullmatch(r"^\w+ bows before \w+\.$", line) is not None:
            return "emote_bow_other"
        elif re.fullmatch(r"^\w+ thanks \w+ heartily\.$", line) is not None:
            return "emote_thank_other"
        elif re.fullmatch(r"^\w+ waves at \w+\.$", line) is not None:
            return "emote_wave_other"
        elif (
            re.fullmatch(
                r"^\w+ grabs hold of \w+ and begins to dance with (?:h(?:er|im)|it)\.$",
                line,
            )
            is not None
        ):
            return "emote_dance_other"
        elif re.fullmatch(r"^\w+ bonks \w+ on the head\!$", line) is not None:
            return "emote_bonk_other"
        elif re.fullmatch(r"^\w+ beams a smile at (a|) \w+$", line) is not None:
            return "emote_smile_other"
        elif re.fullmatch(r"^\w+ cheers at \w+$", line) is not None:
            return "emote_cheer_other"

        return None

    except Exception as e:
        eqa_settings.log(
            "process_log (check_emotes): Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def check_who(line):
    """
    Check line for who output
    """

    try:
        if re.fullmatch(r"^Players (on|in) EverQuest\:$", line) is not None:
            return "who_top"
        elif re.fullmatch(r"^Friends currently on EverQuest\:$", line) is not None:
            return "who_top_friends"
        elif re.fullmatch(r"^Players Looking For Groups\:$", line) is not None:
            return "who_top_lfg"
        elif (
            re.fullmatch(
                r"^\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-$", line
            )
            is not None
        ):
            return "who_line"
        elif (
            re.fullmatch(
                r"^\[\d+ (?:(?:(?:Shadow )?Knigh|Hierophan|Revenan)t|(?:Elemental|Phantasm)ist|High Priest|Illusionist|(?:Grandmast|P(?:athfind|reserv)|C(?:hannel|avali)|(?:Enchan|Mas)t|(?:Begu|Def)il|Conjur|Sorcer|Wa(?:nder|rd)|(?:Crusa|Outri)d|Rang|Evok|Reav)er|Necromancer|(?:B(?:lackgu)?|Wiz)ard|Grave Lord|(?:T(?:roubadou|empla)|Warrio|Vica)r|A(?:rch Mage|ssassin)|Minstrel|Virtuoso|(?:(?:Myrmid|Champi)o|Magicia|Shama)n|(?:Discipl|Oracl|R(?:ogu|ak))e|Luminary|Warlock|Heretic|Paladin|(?:Warlor|Drui)d|Cleric|Mystic|Monk)\] \w+ \((?:Barbarian|Halfling|Half\-Elf|(?:Dark|High) Elf|Wood Elf|Skeleton|Erudite|Iksar|Troll|(?:Gnom|Ogr)e|Dwarf|Human)\)(?:( \<[a-zA-Z\s]+\> ZONE\: \w+| \<[a-zA-Z\s]+\>|))$",
                line,
            )
            is not None
        ):
            return "who_player"
        elif (
            re.fullmatch(
                r"^AFK \[\d+ (?:(?:(?:Shadow )?Knigh|Hierophan|Revenan)t|(?:Elemental|Phantasm)ist|High Priest|Illusionist|(?:Grandmast|P(?:athfind|reserv)|C(?:hannel|avali)|(?:Enchan|Mas)t|(?:Begu|Def)il|Conjur|Sorcer|Wa(?:nder|rd)|(?:Crusa|Outri)d|Rang|Evok|Reav)er|Necromancer|(?:B(?:lackgu)?|Wiz)ard|Grave Lord|(?:T(?:roubadou|empla)|Warrio|Vica)r|A(?:rch Mage|ssassin)|Minstrel|Virtuoso|(?:(?:Myrmid|Champi)o|Magicia|Shama)n|(?:Discipl|Oracl|R(?:ogu|ak))e|Luminary|Warlock|Heretic|Paladin|(?:Warlor|Drui)d|Cleric|Mystic|Monk)\] \w+ \((?:Barbarian|Halfling|Half\-Elf|(?:Dark|High) Elf|Wood Elf|Skeleton|Erudite|Iksar|Troll|(?:Gnom|Ogr)e|Dwarf|Human)\)(?:( \<[a-zA-Z\s]+\> ZONE\: \w+| \<[a-zA-Z\s]+\>|))$",
                line,
            )
            is not None
        ):
            return "who_player_afk"
        elif (
            re.fullmatch(
                r"^\<LINKDEAD\>\[\d+ (?:(?:(?:Shadow )?Knigh|Hierophan|Revenan)t|(?:Elemental|Phantasm)ist|High Priest|Illusionist|(?:Grandmast|P(?:athfind|reserv)|C(?:hannel|avali)|(?:Enchan|Mas)t|(?:Begu|Def)il|Conjur|Sorcer|Wa(?:nder|rd)|(?:Crusa|Outri)d|Rang|Evok|Reav)er|Necromancer|(?:B(?:lackgu)?|Wiz)ard|Grave Lord|(?:T(?:roubadou|empla)|Warrio|Vica)r|A(?:rch Mage|ssassin)|Minstrel|Virtuoso|(?:(?:Myrmid|Champi)o|Magicia|Shama)n|(?:Discipl|Oracl|R(?:ogu|ak))e|Luminary|Warlock|Heretic|Paladin|(?:Warlor|Drui)d|Cleric|Mystic|Monk)\] \w+ \((?:Barbarian|Halfling|Half\-Elf|(?:Dark|High) Elf|Wood Elf|Skeleton|Erudite|Iksar|Troll|(?:Gnom|Ogr)e|Dwarf|Human)\)(?:( \<[a-zA-Z\s]+\> ZONE\: \w+| \<[a-zA-Z\s]+\>|))$",
                line,
            )
            is not None
        ):
            return "who_player_linkdead"
        elif (
            re.fullmatch(
                r"^\[ANONYMOUS\] \w+ (?:( \<[a-zA-Z\s]+\>))$(?:( \<[a-zA-Z\s]+\> ZONE\: \w+| \<[a-zA-Z\s]+\>|)",
                line,
            )
            is not None
        ):
            return "who_player_anon"
        elif (
            re.fullmatch(
                r"^\<LINKDEAD\>\[ANONYMOUS\] \w+ (?:( \<[a-zA-Z\s]+\>))$(?:( \<[a-zA-Z\s]+\> ZONE\: \w+| \<[a-zA-Z\s]+\>|)",
                line,
            )
            is not None
        ):
            return "who_player_anon_linkdead"
        elif (
            re.fullmatch(
                r"^There (is|are) \d+ (player|players) in [a-zA-Z\s]+\.$", line
            )
            is not None
        ):
            return "who_total"
        elif (
            re.fullmatch(
                r"^There are no players in EverQuest that match those who filters\.$",
                line,
            )
            is not None
        ):
            return "who_total_empty"
        elif (
            re.fullmatch(
                r"^There are no players in [a-zA-Z\s]+ that match those who filters\.$",
                line,
            )
            is not None
        ):
            return "who_total_local_empty"

        return None

    except Exception as e:
        eqa_settings.log(
            "process_log (check_who): Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def check_pets(line):
    """
    Check line for pet responses
    """

    try:
        if (
            re.fullmatch(r"^[a-zA-Z\s]+ says, \'Following you, Master\.\'", line)
            is not None
        ):
            return "pet_follow"
        elif (
            re.fullmatch(
                r"^[a-zA-Z\s]+ says, \'No longer taunting attackers, Master\.\'", line
            )
            is not None
        ):
            return "pet_taunt_off"
        elif (
            re.fullmatch(r"^[a-zA-Z\s]+ says, \'At your service Master\.\'", line)
            is not None
        ):
            return "pet_spawn"
        elif (
            re.fullmatch(r"^[a-zA-Z\s]+ says, \'Changing position, Master\.\'", line)
            is not None
        ):
            return "pet_sit_stand"
        elif (
            re.fullmatch(
                r"^[a-zA-Z\s]+ says, \'Guarding with my life\.\.oh splendid one\.\'",
                line,
            )
            is not None
        ):
            return "pet_guard"
        elif (
            re.fullmatch(
                r"^[a-zA-Z\s]+ says, \'Sorry, Master\.\.calming down\.\'", line
            )
            is not None
        ):
            return "pet_back"
        elif (
            re.fullmatch(
                r"^[a-zA-Z\s]+ says, \'That is not a legal target master\.\'", line
            )
            is not None
        ):
            return "pet_illegal_target"

        return None

    except Exception as e:
        eqa_settings.log(
            "process_log (check_pets): Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


if __name__ == "__main__":
    main()
