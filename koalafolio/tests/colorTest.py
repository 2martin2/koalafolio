import koalafolio.gui.QStyle as style

color = [75, 180, 255]
colors = [color]
for i in range(1, 20):
    colors.append(style.nextColor(color, i*55))
    print(str(colors[-1]).replace('[','').replace(']',''))