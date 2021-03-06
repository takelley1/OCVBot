# coding=UTF-8
"""
Contains all functions related to training skills.

"""
import logging as log

from ocvbot import behavior, vision as vis, misc, startup as start, input


def wait_for_level_up(wait_time):
    """
    Waits the specified number of seconds for a level-up message to
    appear in the chat menu.

    Args:
        wait_time: Approximately the number of seconds to wait for a
                   level-up message to appear. Checks for a level-up
                   message about once every second.

    Returns:
        If a level-up message appears, returns True.
        Returns False otherwise.

    """
    log.info('Checking for level-up')
    level_up = vis.Vision(region=vis.chat_menu,
                          needle='./needles/chat-menu/level-up.png',
                          loop_num=wait_time,
                          loop_sleep_range=(900, 1100)).wait_for_needle()
    if level_up is True:
        return True
    else:
        return False


class Cooking:
    """
    Class for all functions related to training the Cooking skill.

    Args:
        item_inv (file): Filepath to the food to cook as it appears in
                         the player's inventory. This is the raw version.
        item_bank (file): Filepath to the food to cook as it appears in
                          the players' bank. Make sure this image doesn't
                          include the stack count if this item is stacked.
        heat_source (file): Filepath to the fire or range to cook the
                            item with as it appears in the game world.

    """

    def __init__(self, item_inv, item_bank, heat_source):
        self.item_inv = item_inv
        self.item_bank = item_bank
        self.heat_source = heat_source

    def cook_item(self):
        """
        Cooks all instances of the given food in the player's inventory.

        Returns:
            Returns True if all items were cooked. Returns False in all
            other cases.

        """
        behavior.open_side_stone('inventory')
        # Select the raw food in the inventory.
        # Confidence must be higher than normal since raw food is very
        #   similar in appearance to its cooked version.
        item_selected = vis.Vision(region=vis.client,
                                   needle=self.item_inv,
                                   loop_num=3,
                                   conf=0.99).click_needle()
        if item_selected is False:
            log.error('Unable to find item!')
            return False

        # Select the range or fire.
        heat_source_selected = vis.Vision(region=vis.game_screen,
                                          needle=self.heat_source,
                                          loop_num=3,
                                          loop_sleep_range=(500, 1000),
                                          conf=0.85).click_needle()
        if heat_source_selected is False:
            log.error('Unable to find heat source!')
            return False

        misc.sleep_rand_roll(chance_range=(15, 35), sleep_range=(1000, 10000))

        # Wait for the "how many of this item do you want to cook" chat
        #   menu to appear.
        do_x_screen = vis.Vision(region=vis.chat_menu,
                                 needle='./needles/chat-menu/do-x.png',
                                 loop_num=30,
                                 loop_sleep_range=(500, 1000)).wait_for_needle()
        if do_x_screen is False:
            log.error('Timed out waiting for "Make X" screen!')
            return False

        # Begin cooking food.
        input.Keyboard().keypress(key='space')
        misc.sleep_rand(3000, 5000)

        # Wait for either a level-up or for the player to stop cooking.
        # To determine when the player is done cooking, look for the
        #   bright blue "Staff of Water" orb to re-appear (equipped weapons
        #   disappear while cooking food). The player must have this item
        #   equipped.
        for _ in range(1, 60):
            misc.sleep_rand(1000, 3000)
            level_up = wait_for_level_up(1)
            # If the player levels-up while cooking, restart cooking.
            if level_up is True:
                self.cook_item()
            cooking_done = vis.Vision(region=vis.game_screen,
                                      needle='./needles/game-screen/staff-of-water-top.png',
                                      conf=0.9,
                                      loop_num=1).wait_for_needle()
            if cooking_done is True:
                break

        misc.sleep_rand_roll(chance_range=(15, 35), sleep_range=(20000, 120000))
        return True


class Magic:
    """
    Class for all activities related to training the Magic skill.

    Args:
        spell (file): Filepath to the spell to cast as it appears in the
                      player's spellbook (NOT greyed-out).
        target (file): Filepath to the target to cast the spell on as it
                       appears in the game world. If the spell is a non-
                       combat spell, this would be an item as it appears
                       in the player's inventory.
        conf (float): Confidence required to match the target.
        region (tuple): The coordinate region to use when searching for
                        the target. This will either be "vis.inv" or
                        "vis.game_screen".
        inventory (bool): Whether the spell is being cast on an item in
                          the player's inventory (as opposed to a monster),
                          default is False.
        move_duration_range (tuple): A 2-tuple of the minimum and maximum
                                     number of miliseconds the mouse cursor
                                     will take while moving to the spell
                                     icon and the target, default is
                                     (10, 1000).
        logout (bool): Whether to logout once out of runes or the
                       target cannot be found, default is False.

    """

    def __init__(self, spell, target, conf, region, inventory=False,
                 move_duration_range=(10, 1000), logout=False):
        self.spell = spell
        self.target = target
        self.conf = conf
        self.region = region
        self.inventory = inventory
        self.move_duration_range = move_duration_range
        self.logout = logout

    def _select_spell(self):
        """
        Activate the desired spell.

        Returns:
            Returns True if spell was activated, False if otherwise.

        """
        for _ in range(1, 5):
            spell_available = vis.Vision(needle=self.spell, region=vis.inv, loop_num=30) \
                .click_needle(sleep_range=(50, 800, 50, 800,),
                              move_duration_range=self.move_duration_range)
            if spell_available is False:
                behavior.open_side_stone('spellbook')
                misc.sleep_rand(100, 300)
            else:
                return True
        return False

    def _select_target(self):
        """
        Attempt to find the target to cast the spell on. Can be either a
        monster in the game world or an item in the inventory.

        Returns:
            Returns True if target was found and selected, False if
            otherwise.

        """

        for _ in range(1, 5):
            target = vis.Vision(needle=self.target, region=self.region,
                                loop_num=10, conf=self.conf) \
                .click_needle(sleep_range=(10, 500, 10, 500,),
                              move_duration_range=self.move_duration_range)

            if target is False:
                # Make sure the inventory is active when casting on items.
                if self.inventory is True:
                    behavior.open_side_stone('inventory')
                if vis.orient()[0] == 'logged_out':
                    behavior.login_full()
                misc.sleep_rand(1000, 3000)
            else:
                return True
        return False

    def cast_spell(self):
        """
        Cast a spell at a target.

        Returns:
            Returns True if spell was cast, False if otherwise.

        """
        spell_selected = self._select_spell()
        if spell_selected is False:
            if self.logout is True:
                log.critical('Out of runes! Logging out in 10-20 seconds!')
                misc.sleep_rand(10000, 20000)
                behavior.logout()
            else:
                log.critical('All done!')
                return False

        target_selected = self._select_target()
        if target_selected is False:
            if self.logout is True:
                log.critical('Unable to find target! Logging out in 10-20 seconds!')
                misc.sleep_rand(10000, 20000)
                behavior.logout()
            else:
                log.critical('All done!')
                return False

        # Wait for spell to be cast.
        misc.sleep_rand(int(start.config['magic']['min_cast_delay']),
                        int(start.config['magic']['max_cast_delay']))
        # Roll for random wait.
        misc.sleep_rand_roll(chance_range=(100, 400))

        if self.logout is True:
            # Roll for logout after the configured period of time.
            behavior.logout_break_range()

        return True


class Mining:
    """
    Class for all activities related to training the Mining skill.

    Args:
        rocks (list): A list containing an arbitrary number of 2-tuples.
                       Each tuple must contain two filepaths:
                       The first filepath must be a needle of the
                       rock in its "full" state. The second filepath
                       must be a needle of the same rock in its "empty"
                       state.
        ore (file): Filepath to a needle of the item icon of the ore
                    being mined, as it appears in the player's
                    inventory.

    """
    # Create a list of tuples to determine which items to drop
    drop_items = [(bool(start.config['mining']['drop_sapphire']), './needles/items/uncut-sapphire.png'),
                  (bool(start.config['mining']['drop_emerald']), './needles/items/uncut-emerald.png'),
                  (bool(start.config['mining']['drop_ruby']), './needles/items/uncut-ruby.png'),
                  (bool(start.config['mining']['drop_diamond']), './needles/items/uncut-diamong.png'),
                  (bool(start.config['mining']['drop_clue_geode']), './needles/items/clue-geode.png')]

    def __init__(self, rocks, ore, position=None, conf=(0.8, 0.85)):
        self.rocks = rocks
        self.ore = ore
        self.position = position
        self.conf = conf

        if position is not None:
            behavior.travel(position[0], position[1])

    def mine_rocks(self):
        """
        Mines the provided rocks until inventory is full.

        This function alternates mining among the rocks that were provided
        (it can mine one rock, two rocks, or many rocks at once).
        All rocks must be of the same ore type.

        Returns:
            Returns True if a full inventory of ore was mined and banked or
            dropped, or if script timed out looking for ore.

        """
        # TODO: Count the number of items in the inventory to make sure
        #   the function never receives an "inventory is already full" message.

        # Make sure inventory is selected.
        behavior.open_side_stone('inventory')

        for tries in range(100):

            for rock_needle in self.rocks:
                # Unpack each tuple in the rocks[] list to obtain the "full"
                #   and "empty" versions of each ore.
                (full_rock_needle, empty_rock_needle) = rock_needle

                log.debug('Searching for ore %s...', tries)

                # If current rock is full, begin mining it.
                # Move the mouse away from the rock so it doesn't
                #   interfere with matching the needle.
                rock_full = vis.Vision(region=vis.game_screen, loop_num=1,
                                       needle=full_rock_needle, conf=self.conf[0]) \
                    .click_needle(sleep_range=(0, 100, 0, 100,),
                                  move_duration_range=(0, 500), move_away=True)

                if rock_full is True:
                    log.info('Waiting for mining to start.')
                    misc.sleep_rand_roll(chance_range=(1, 200))

                    # Once the rock has been clicked on, wait for mining to
                    #   start by monitoring chat messages.
                    mining_started = vis.Vision(region=vis.chat_menu_recent, loop_num=5, conf=0.9,
                                                needle='./needles/chat-menu/mining-started.png',
                                                loop_sleep_range=(100, 200)).wait_for_needle()

                    # If mining hasn't started after looping has finished,
                    #   check to see if the inventory is full.
                    if mining_started is False:
                        log.debug('Timed out waiting for mining to start.')

                        inv_full = vis.Vision(region=vis.chat_menu, loop_num=1,
                                              needle='./needles/chat-menu/mining-inventory-full.png'). \
                            wait_for_needle()

                        # If the inventory is full, empty the ore and
                        #   return.
                        if inv_full is True:
                            return 'inventory-full'

                    log.debug('Mining started.')

                    # Wait until the rock is empty by waiting for the
                    #   "empty" version of the rock_needle tuple.
                    rock_empty = vis.Vision(region=vis.game_screen, loop_num=35,
                                            conf=self.conf[1], needle=empty_rock_needle,
                                            loop_sleep_range=(100, 200)).wait_for_needle()

                    if rock_empty is True:
                        log.info('Rock is empty.')
                        log.debug('%s empty.', rock_needle)
                        behavior.human_behavior_rand(chance=100)
                    else:
                        log.info('Timed out waiting for mining to finish.')
        return True

    def drop_inv_ore(self):
        """
        Drops ore and optionally gems from inventory.

        Returns:
            Returns True if ore has been dropped.

        """
        ore_dropped = behavior.drop_item(item=self.ore)

        if ore_dropped is False:
            behavior.logout()
            # This runtime error will occur if the
            #   player's inventory is full, but they
            #   don't have any ore to drop.
            raise Exception('Could not find ore to drop!')

        # Iterate through the other items that could
        #   be dropped. If any of them is true, drop that item.
        # The for loop is iterating over a tuple of tuples.
        for item in self.drop_items:
            # Unpack the tuple
            (drop_item_bool, path) = item
            if drop_item_bool is True:
                behavior.drop_item(item=str(path), track=False)
                return True
