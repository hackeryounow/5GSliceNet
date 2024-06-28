from network.slice_nets import SliceNetModeOne, CommonSliceNetModeTwo, CommonSliceNetModeThree, CommonSliceNetModeFour

slice = SliceNetModeOne(2, ["internet", "internet"])
slice.configure()
slice.to_dict()
# slice2 = SliceNetModeTwo(2, ["internet", "internet"])
# slice2.to_dict()
# slice3 = SliceNetModeFour(1, ["internet"])
# slice3.to_dict()
