from network.slice_nets import SliceNetModeOne, SliceNetModeTwo, SliceNetModeThree, SliceNetModeFour

# slice = SliceNetModeOne(2, ["internet", "internet"], path="5gc_mode1_1")
# slice.configure()
# slice2 = SliceNetModeTwo(2, ["internet", "internet"])
# slice2.configure()
# slice3 = SliceNetModeThree(1, ["internet"], 2)
# slice3.configure()
slice4 = SliceNetModeFour(1, ["internet"])
slice4.configure()
