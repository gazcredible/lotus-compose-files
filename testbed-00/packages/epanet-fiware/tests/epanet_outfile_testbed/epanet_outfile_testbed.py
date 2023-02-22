import epanet_fiware.epanet_outfile_handler

if __name__ == '__main__':
    quitApp = False

    bin_file = epanet_fiware.epanet_outfile_handler.EpanetOutFile('epanet.bin')

    #I want a resource (link or node)
    #get info for a sim frame
    print('Nodes:' + str(bin_file.node_count()))
    print('Links:' + str(bin_file.link_count()))

    print('Periods:' + str(bin_file.reporting_periods()))

    node = 100
    period = 10

    text = 'Node: ' + str(node) + ' Period: ' +str(period)
    text += '\n'
    text += 'Demand: ' + str(round(bin_file.node_supply(period, node),2))
    text += '\n'
    text += 'Head: ' + str(round(bin_file.node_head(period, node),2))
    text += '\n'
    text += 'Pressure: ' + str(round(bin_file.node_pressure(period, node),2))
    text += '\n'
    text += 'Quality: ' + str(round(bin_file.node_quality(period, node),2))
    text += '\n'

    print(text)

    link = 100
    text = 'Link: ' + str(link) + ' Period: ' + str(period)
    text += '\n'
    text += 'Flow: ' + str(round(bin_file.link_flow(period, link),2) )
    text += '\n'
    text += 'Velocity: ' + str(round(bin_file.link_velocity(period, link),2) )
    text += '\n'
    text += 'Headloss: ' + str(round(bin_file.link_headloss(period, link),2) )
    text += '\n'
    text += 'Qualiy: ' + str(round(bin_file.link_quality(period, link),2) )
    text += '\n'
    text += 'Status: ' + str(round(bin_file.link_status(period, link),2) )
    text += '\n'
    text += 'Setting: ' + str(round(bin_file.link_setting(period, link),2) )
    text += '\n'
    text += 'Reaction: ' + str(round(bin_file.link_reaction(period, link),2) )
    text += '\n'
    text += 'Friction: ' + str(round(bin_file.link_friction(period, link),2) )
    text += '\n'

    print(text)


    while quitApp is False:
        print('\n')
        print('1..get_chart_prop_by_sensor')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            pass

        if key == 'x':
            quitApp = True