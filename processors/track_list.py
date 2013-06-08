from target import Target
import math

class TrackList(object):
    def __init__(self):
        self.tracks = []

    def processDetection(self, pos):
        associated = self.associateTrack(pos)
        if not associated:
            self.tracks.append(Target(pos))

    def associateTrack(self, pos):
        for track in self.tracks:
            gate_w = track.kalman.measurement_noise_cov
	    gate_y = 0.075
            # debug only will delete when done
            #print "pos[0]:%f pos[1]:%f gate[0,0]:%f gate[1,0]:%f gate[0,1]:%f \
            #      gate[1,1]:%f" % (pos[0],pos[1],gate_w[0,0],gate_w[1,0],     \
            #      gate_w[0,1],gate_w[1,1])
            if pos[0] > track.prediction[0] - gate_w[0,0]           \
                    and pos[0] < track.prediction[0] + gate_w[0,0]  \
                    and pos[1] > track.prediction[1] - gate_w[1,0]  \
                    and pos[1] < track.prediction[1] + gate_w[1,0]:
	    #The below comments are for additional testing if the above method 
            # doest work
	    #dist = distance(pos,track.prediction)
            #if dist < 0.075:
            #    track.update(pos)
                return True
        # Got through the whole track list without a hit
        return False

def distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)


#if __name__ == '__main__':
    #TODO: UNIT TEST
    #return
