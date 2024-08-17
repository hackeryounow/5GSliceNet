from network.slice_nets import SliceNetModeOne, SliceNetModeTwo, SliceNetModeThree, SliceNetModeFour

# slice1 = SliceNetModeOne(2, ["internet", "internet"], path="5gc_mode1_1")
# slice1.configure()
# slice2 = SliceNetModeTwo(2, ["internet", "internet"], path="5gc_mode2_1")
# slice2.configure()
# slice3 = SliceNetModeThree(1, ["internet"], 2)
# slice3.configure()
slice4 = SliceNetModeFour(1, ["internet"], path="5gc_mode4_1")
slice4.configure()
