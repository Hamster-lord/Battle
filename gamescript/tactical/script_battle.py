import csv
import os
import random

import numpy as np
import pygame

from gamescript.tactical.script_other import board_pos

battle_side_cal = (1, 0.5, 0.1, 0.5)  # battle_side_cal is for melee combat side modifier


def check_split(self, who):
    """Check if unit can be splitted, if not remove splitting button"""
    # v split by middle column
    if np.array_split(who.subunit_list, 2, axis=1)[0].size >= 10 and np.array_split(who.subunit_list, 2, axis=1)[1].size >= 10 and \
            who.leader[1].name != "None":  # can only split if both unit size will be larger than 10 and second leader exist
        self.battle_ui.add(self.col_split_button)
    elif self.col_split_button in self.battle_ui:
        self.battle_ui.remove(self.col_split_button)
    # ^ End col

    # v split by middle row
    if np.array_split(who.subunit_list, 2)[0].size >= 10 and np.array_split(who.subunit_list, 2)[1].size >= 10 and \
            who.leader[1].name != "None":
        self.battle_ui.add(self.row_split_button)
    elif self.row_split_button in self.battle_ui:
        self.battle_ui.remove(self.row_split_button)


def add_unit(subunitlist, position, gameid, colour, leaderlist, leaderstat, control, coa, command, startangle, starthp, startstamina, team):
    """Create unit object into the battle and leader of the unit"""
    from gamescript import unit, leader
    oldsubunitlist = subunitlist[~np.all(subunitlist == 0, axis=1)]  # remove whole empty column in subunit list
    subunitlist = oldsubunitlist[:, ~np.all(oldsubunitlist == 0, axis=0)]  # remove whole empty row in subunit list
    unit = unit.Unit(position, gameid, subunitlist, colour, control, coa, command, abs(360 - startangle), starthp, startstamina, team)

    # add leader
    unit.leader = [leader.Leader(leaderlist[0], leaderlist[4], 0, unit, leaderstat),
                   leader.Leader(leaderlist[1], leaderlist[5], 1, unit, leaderstat),
                   leader.Leader(leaderlist[2], leaderlist[6], 2, unit, leaderstat),
                   leader.Leader(leaderlist[3], leaderlist[7], 3, unit, leaderstat)]
    return unit


def generate_unit(battle, which_army, row, control, command, colour, coa, subunit_game_id):
    """generate unit data into self object
    row[1:9] is subunit troop id array, row[9][0] is leader id and row[9][1] is position of sub-unt the leader located in"""
    from gamescript import unit, subunit
    this_unit = add_unit(np.array([row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]]), (row[9][0], row[9][1]), row[0],
                         colour, row[10] + row[11], battle.leader_stat, control,
                         coa, command, row[13], row[14], row[15], row[16])
    which_army.add(this_unit)
    army_subunit_index = 0  # army_subunit_index is list index for subunit list in a specific army

    # v Setup subunit in unit to subunit group
    row, column = 0, 0
    max_column = len(this_unit.subunit_list[0])
    for subunit_number in np.nditer(this_unit.subunit_list, op_flags=["readwrite"], order="C"):
        if subunit_number != 0:
            add_subunit = subunit.Subunit(subunit_number, subunit_game_id, this_unit, this_unit.subunit_position_list[army_subunit_index],
                                         this_unit.start_hp, this_unit.start_stamina, battle.unitscale)
            battle.subunit.add(add_subunit)
            add_subunit.board_pos = board_pos[army_subunit_index]
            subunit_number[...] = subunit_game_id
            this_unit.subunit_sprite_array[row][column] = add_subunit
            this_unit.subunit_sprite.append(add_subunit)
            subunit_game_id += 1
        else:
            this_unit.subunit_sprite_array[row][column] = None  # replace numpy None with python None

        column += 1
        if column == max_column:
            column = 0
            row += 1
        army_subunit_index += 1
    battle.troop_number_sprite.add(unit.TroopNumber(battle.screen_scale, this_unit))  # create troop number text sprite

    return subunit_game_id


def unit_setup(gamebattle):
    """read unit from unit_pos(source) file and create object with addunit function"""
    main_dir = gamebattle.main_dir
    # defaultunit = np.array([[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],
    # [0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]])

    team_colour = gamebattle.team_colour
    team_army = (gamebattle.team0_unit, gamebattle.team1_unit, gamebattle.team2_unit)

    with open(os.path.join(main_dir, "data", "ruleset", gamebattle.ruleset_folder, "map",
                           gamebattle.mapselected, gamebattle.source, gamebattle.genre, "unit_pos.csv"), encoding="utf-8", mode="r") as unitfile:
        rd = csv.reader(unitfile, quoting=csv.QUOTE_ALL)
        subunit_game_id = 1
        for row in rd:
            for n, i in enumerate(row):
                if i.isdigit():
                    row[n] = int(i)
                if n in range(1, 12):
                    row[n] = [int(item) if item.isdigit() else item for item in row[n].split(",")]

            control = False
            if gamebattle.playerteam == row[16] or gamebattle.enactment:  # player can control only his team or both in enactment mode
                control = True

            colour = team_colour[row[16]]
            which_army = team_army[row[16]]

            command = False  # Not commander unit by default
            if len(which_army) == 0:  # First unit is commander
                command = True
            coa = pygame.transform.scale(gamebattle.coa_list[row[12]], (60, 60))  # get coa_list image and scale smaller to fit ui
            subunit_game_id = generate_unit(gamebattle, which_army, row, control, command, colour, coa, subunit_game_id)
            # ^ End subunit setup

    unitfile.close()


def loss_cal(attacker, defender, hit, defence, dmgtype, defside=None):
    """Calculate dmg, type 0 is melee attack and will use attacker subunit stat,
    type that is not 0 will use the type object stat instead (mostly used for range attack)"""
    who = attacker
    target = defender

    height_advantage = who.height - target.height
    if dmgtype != 0:
        height_advantage = int(height_advantage / 2)  # Range attack use less height advantage
    hit += height_advantage

    if defence < 0 or who.ignore_def:  # Ignore def trait
        defence = 0

    hit_chance = hit - defence
    if hit_chance < 0:
        hit_chance = 0
    elif hit_chance > 80:  # Critical hit
        hit_chance *= who.crit_effect  # modify with crit effect further
        if hit_chance > 200:
            hit_chance = 200
    else:  # infinity number can cause nan value
        hit_chance = 200

    combat_score = round(hit_chance / 100, 1)
    if combat_score == 0 and random.randint(0, 10) > 9:  # Final chance to not miss
        combat_score = 0.1

    if combat_score > 0:
        leader_dmg_bonus = 0
        if who.leader is not None:
            leader_dmg_bonus = who.leader.combat  # Get extra dmg from leader combat stat

        if dmgtype == 0:  # Melee melee_dmg
            dmg = random.uniform(who.melee_dmg[0], who.melee_dmg[1])
            if who.charge_skill in who.skill_effect:  # Include charge in melee_dmg if attacking
                if who.ignore_chargedef is False:  # Ignore charge defence if have ignore trait
                    side_cal = battle_side_cal[defside]
                    if target.full_def or target.temp_full_def:  # defence all side
                        side_cal = 1
                    dmg = dmg + ((who.charge - (target.charge_def * side_cal)) * 2)
                    if (target.charge_def * side_cal) >= who.charge / 2:
                        who.charge_momentum = 1  # charge get stopped by charge def
                    else:
                        who.charge_momentum -= (target.charge_def * side_cal) / who.charge
                else:
                    dmg = dmg + (who.charge * 2)
                    who.charge_momentum -= 1 / who.charge

            if target.charge_skill in target.skill_effect:  # Also include charge_def in melee_dmg if enemy charging
                if target.ignore_chargedef is False:
                    charge_def_cal = who.charge_def - target.charge
                    if charge_def_cal < 0:
                        charge_def_cal = 0
                    dmg = dmg + (charge_def_cal * 2)  # if charge def is higher than enemy charge then deal back additional melee_dmg
            elif who.charge_skill not in who.skill_effect:  # not charging or defend from charge, use attack speed roll
                dmg += sum([random.uniform(who.melee_dmg[0], who.melee_dmg[1]) for x in range(who.melee_speed)])

            penetrate = who.melee_penetrate / target.armour
            if penetrate > 1:
                penetrate = 1
            dmg = dmg * penetrate * combat_score

        else:  # Range Damage
            penetrate = dmgtype.penetrate / target.armour
            if penetrate > 1:
                penetrate = 1
            dmg = dmgtype.dmg * penetrate * combat_score

        leader_dmg = dmg
        unit_dmg = (dmg * who.troop_number) + leader_dmg_bonus  # dmg on subunit is dmg multiply by troop number with addition from leader combat
        if (who.anti_inf and target.subunit_type in (1, 2)) or (who.anti_cav and target.subunit_type in (4, 5, 6, 7)):  # Anti trait dmg bonus
            unit_dmg = unit_dmg * 1.25

        morale_dmg = dmg / 50

        # Damage cannot be negative (it would heal instead), same for morale and leader dmg
        if unit_dmg < 0:
            unit_dmg = 0
        if leader_dmg < 0:
            leader_dmg = 0
        if morale_dmg < 0:
            morale_dmg = 0
    else:  # complete miss
        unit_dmg = 0
        leader_dmg = 0
        morale_dmg = 0

    return unit_dmg, morale_dmg, leader_dmg


def apply_status_to_enemy(status_list, inflict_status, receiver, attacker_side, receiver_side):
    """apply aoe status effect to enemy subunits"""
    for status in inflict_status.items():
        if status[1] == 1 and attacker_side == 0:  # only front enemy
            receiver.status_effect[status[0]] = status_list[status[0]].copy()
        elif status[1] == 2:  # aoe effect to side enemy
            receiver.status_effect[status[0]] = status_list[status[0]].copy()
            if status[1] == 3:  # apply to corner enemy subunit (left and right of self front enemy subunit)
                corner_enemy_apply = receiver.nearby_subunit_list[0:2]
                if receiver_side in (1, 2):  # attack on left/right side means corner enemy would be from front and rear side of the enemy
                    corner_enemy_apply = [receiver.nearby_subunit_list[2], receiver.nearby_subunit_list[5]]
                for this_subunit in corner_enemy_apply:
                    if this_subunit != 0:
                        this_subunit.status_effect[status[0]] = status_list[status[0]].copy()
        elif status[1] == 3:  # whole unit aoe
            for this_subunit in receiver.unit.subunit_sprite:
                if this_subunit.state != 100:
                    this_subunit.status_effect[status[0]] = status_list[status[0]].copy()


def complex_dmg_cal(attacker, receiver, dmg, morale_dmg, leader_dmg, dmg_effect, timer_mod):
    final_dmg = round(dmg * dmg_effect * timer_mod)
    final_morale_dmg = round(morale_dmg * dmg_effect * timer_mod)
    if final_dmg > receiver.unit_health:  # dmg cannot be higher than remaining health
        final_dmg = receiver.unit_health

    receiver.unit_health -= final_dmg
    health_check = 0.1
    if receiver.max_health != infinity:
        health_check = 1 - (receiver.unit_health / receiver.max_health)
    receiver.base_morale -= (final_morale_dmg + attacker.bonus_morale_dmg) * receiver.mental * health_check
    receiver.stamina -= attacker.bonus_stamina_dmg

    # v Add red corner to indicate combat
    if receiver.red_border is False:
        receiver.block.blit(receiver.images[11], receiver.corner_image_rect)
        receiver.red_border = True
    # ^ End red corner

    if attacker.elem_melee not in (0, 5):  # apply element effect if atk has element, except 0 physical, 5 magic
        receiver.elem_count[attacker.elem_melee - 1] += round(final_dmg * (100 - receiver.elem_res[attacker.elem_melee - 1] / 100))

    attacker.base_morale += round((final_morale_dmg / 5))  # recover some morale when deal morale dmg to enemy

    if receiver.leader is not None and receiver.leader.health > 0 and random.randint(0, 10) > 9:  # dmg on subunit leader, only 10% chance
        final_leader_dmg = round(leader_dmg - (leader_dmg * receiver.leader.combat / 101) * timer_mod)
        if final_leader_dmg > receiver.leader.health:
            final_leader_dmg = receiver.leader.health
        receiver.leader.health -= final_leader_dmg


def dmg_cal(attacker, target, attacker_side, target_side, status_list, combat_timer):
    """base_target position 0 = Front, 1 = Side, 3 = Rear, attacker_side and target_side is the side attacking and defending respectively"""
    who_luck = random.randint(-50, 50)  # attacker luck
    target_luck = random.randint(-50, 50)  # defender luck
    who_mod = battle_side_cal[attacker_side]  # attacker attack side modifier

    """34 battlemaster full_def or 91 allrounddef status = no flanked penalty"""
    if attacker.full_def or 91 in attacker.status_effect:
        who_mod = 1
    target_percent = battle_side_cal[target_side]  # defender defend side

    if target.full_def or 91 in target.status_effect:
        target_percent = 1

    dmg_effect = attacker.front_dmg_effect
    target_dmg_effect = target.front_dmg_effect

    if attacker_side != 0 and who_mod != 1:  # if attack or defend from side will use discipline to help reduce penalty a bit
        who_mod = battle_side_cal[attacker_side] + (attacker.discipline / 300)
        dmg_effect = attacker.side_dmg_effect  # use side dmg effect as some skill boost only front dmg
        if who_mod > 1:
            who_mod = 1

    if target_side != 0 and target_percent != 1:  # same for the base_target defender
        target_percent = battle_side_cal[target_side] + (target.discipline / 300)
        target_dmg_effect = target.side_dmg_effect
        if target_percent > 1:
            target_percent = 1

    who_hit = float(attacker.attack * who_mod) + who_luck
    who_defence = float(attacker.melee_def * who_mod) + who_luck
    target_hit = float(attacker.attack * target_percent) + target_luck
    target_defence = float(target.melee_def * target_percent) + target_luck

    """33 backstabber ignore def when attack rear side, 55 Oblivious To Unexpected can't defend from rear at all"""
    if (attacker.backstab and target_side == 2) or (target.oblivious and target_side == 2) or (
            target.flanker and attacker_side in (1, 3)):  # Apply only for attacker
        target_defence = 0

    who_dmg, who_morale_dmg, who_leader_dmg = loss_cal(attacker, target, who_hit, target_defence, 0, target_side)  # get dmg by attacker
    target_dmg, target_morale_dmg, target_leader_dmg = loss_cal(target, attacker, target_hit, who_defence, 0, attacker_side)  # get dmg by defender

    timer_mod = combat_timer / 0.5  # Since the update happen anytime more than 0.5 second, high speed that pass by longer than x1 speed will become inconsistent
    complex_dmg_cal(attacker, target, who_dmg, who_morale_dmg, who_leader_dmg, dmg_effect, timer_mod)  # Inflict dmg to defender
    complex_dmg_cal(target, attacker, target_dmg, target_morale_dmg, target_leader_dmg, target_dmg_effect, timer_mod)  # Inflict dmg to attacker

    # v Attack corner (side) of self with aoe attack
    if attacker.corner_atk:
        loop_list = [target.nearby_subunit_list[2], target.nearby_subunit_list[5]]  # Side attack get (2) front and (5) rear nearby subunit
        if target_side in (0, 2):
            loop_list = target.nearby_subunit_list[0:2]  # Front/rear attack get (0) left and (1) right nearby subunit
        for this_subunit in loop_list:
            if this_subunit != 0 and this_subunit.state != 100:
                target_hit, target_defence = float(attacker.attack * target_percent) + target_luck, float(
                    this_subunit.melee_def * target_percent) + target_luck
                who_dmg, who_morale_dmg = loss_cal(attacker, this_subunit, who_hit, target_defence, 0)
                complex_dmg_cal(attacker, this_subunit, who_dmg, who_morale_dmg, who_leader_dmg, dmg_effect, timer_mod)
    # ^ End attack corner

    # v inflict status based on aoe 1 = front only 2 = all 4 side, 3 corner enemy subunit, 4 entire unit
    if attacker.inflict_status != {}:
        apply_status_to_enemy(status_list, attacker.inflict_status, target, attacker_side, target_side)
    if target.inflict_status != {}:
        apply_status_to_enemy(status_list, target.inflict_status, attacker, target_side, attacker_side)
    # ^ End inflict status