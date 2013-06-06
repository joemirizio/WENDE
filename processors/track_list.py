from target import Target

class TrackList(object):
    def __init__(self):
        self.tracks = []

    def processDetection(self, pos):
        associated = self.associateTrack(pos)
        if not associated:
            self.tracks.append(Target(pos))

    def associateTrack(self, pos):
        for track in self.tracks:
            gate_w = track.kalman.measurement_noise_cov[0,0]
            if pos[0] > track.prediction[0] - gate_w           \
                    and pos[0] < track.prediction[0] + gate_w  \
                    and pos[1] > track.prediction[1] - gate_w  \
                    and pos[1] < track.prediction[1] + gate_w:
                track.update(pos)
                return True
        # Got through the whole track list without a hit
        return False

#if __name__ == '__main__':
    #TODO: UNIT TEST
    #return
