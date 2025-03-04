import cv2
import time
import argparse
import os
import torch

import posenet


parser = argparse.ArgumentParser()
parser.add_argument('--model', type=int, default=101)
parser.add_argument('--scale_factor', type=float, default=1.0)
parser.add_argument('--notxt', action='store_true')
parser.add_argument('--image_dir', type=str, default='./images')
parser.add_argument('--output_dir', type=str, default='./output')
args = parser.parse_args()


def main(dd, statte):
    model = posenet.load_model(args.model)
    # model = model.cuda()
    output_stride = model.output_stride

    result = []
    result_s = []

    # if args.output_dir:
    #     if not os.path.exists(args.output_dir):
    #         os.makedirs(args.output_dir)

    # filenames = [
    #     f.path for f in os.scandir(args.image_dir) if f.is_file() and f.path.endswith(('.png', '.jpg'))]

    start = time.time()
    # for f in filenames:
    for iid,d in enumerate(dd):
        print(iid,end=' ... ')
        statte[0] = str(iid)+" / "+str(len(dd))
        input_image, draw_image, output_scale = posenet.utils._process_input(d)
        # input_image, draw_image, output_scale = posenet.read_imgfile(
            # f, scale_factor=args.scale_factor, output_stride=output_stride)
        # print(input_image)
        # print(draw_image)
        # print(output_scale)

        with torch.no_grad():
            input_image = torch.Tensor(input_image)#.cuda()

            heatmaps_result, offsets_result, displacement_fwd_result, displacement_bwd_result = model(input_image)

            pose_scores, keypoint_scores, keypoint_coords = posenet.decode_multiple_poses(
                heatmaps_result.squeeze(0),
                offsets_result.squeeze(0),
                displacement_fwd_result.squeeze(0),
                displacement_bwd_result.squeeze(0),
                output_stride=output_stride,
                max_pose_detections=10,
                min_pose_score=0.25)

        keypoint_coords *= output_scale

        # if args.output_dir:
        draw_image = posenet.draw_skel_and_kp(
            draw_image, pose_scores, keypoint_scores, keypoint_coords,
            min_pose_score=0.25, min_part_score=0.25)

        result += [draw_image]
            # cv2.imwrite(os.path.join(args.output_dir, os.path.relpath(f, args.image_dir)), draw_image)
        

        result_temp = []
        for pi in range(len(pose_scores)):
            if pose_scores[pi] == 0.:
                break
            for ki, (s, c) in enumerate(zip(keypoint_scores[pi, :], keypoint_coords[pi, :, :])):
                result_temp += list(c)

        # print(result_temp)
        if result_temp == []:
            result_temp = [0]*68

        result_s += [result_temp]
        # if not args.notxt:
        #     print()
        #     print("Results for image: %s" % f)
        #     for pi in range(len(pose_scores)):
        #         if pose_scores[pi] == 0.:
        #             break
        #         print('Pose #%d, score = %f' % (pi, pose_scores[pi]))
        #         for ki, (s, c) in enumerate(zip(keypoint_scores[pi, :], keypoint_coords[pi, :, :])):
        #             print('Keypoint %s, score = %f, coord = %s' % (posenet.PART_NAMES[ki], s, c))

    # print('Average FPS:', len(filenames) / (time.time() - start))
    print('Average FPS:', len(dd) / (time.time() - start))

    return result, result_s



if __name__ == "__main__":
    main()