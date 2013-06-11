from target import Target
import math

KNOWN_GATE = 5.0  # for use after at least two detections (known vel)
UNKNOWN_GATE = 3.0  # for use after only one detection (unkown vel)


class TrackList(object):
    def __init__(self):
        self.tracks = []

    def processDetection(self, pos):
        associated = self.associateTrack(pos)
        if not associated:
            self.tracks.append(Target(pos))

    def associateTrack(self, pos):
        i = 0
        for track in self.tracks:
            #gate_w = track.kalman.measurement_noise_cov
            #gate_y = 0.075
            # debug only will delete when done
            #print "pos[0]:%f pos[1]:%f gate[0,0]:%f gate[1,0]:%f gate[0,1]:%f \
            #      gate[1,1]:%f" % (pos[0],pos[1],gate_w[0,0],gate_w[1,0],     \
            #      gate_w[0,1],gate_w[1,1])
            #if pos[0] > track.prediction[0] - gate_w[0,0]           \
            #        and pos[0] < track.prediction[0] + gate_w[0,0]  \
            #        and pos[1] > track.prediction[1] - gate_w[1,0]  \
            #        and pos[1] < track.prediction[1] + gate_w[1,0]:
            #The below comments are for additional testing if the above method
                # doest work
            if track.prediction is not None and \
                    distance(pos, track.prediction) < KNOWN_GATE:
                print 'Det associated: %f from prediction of track %d' % (distance(pos, track.prediction), i)
                track.update(pos)
                return True
            elif track.prediction is None and \
                    distance(pos, track.pos) < UNKNOWN_GATE:
                track.update(pos)
                return True
            i += 1

        # Got through the whole track list without a hit
        print 'Det NOT associated'
        return False


def distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)


#if __name__ == '__main__':
    #TODO: UNIT TEST
    #return
