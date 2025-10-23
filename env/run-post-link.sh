# Pixi unpack doesn't run post-link scripts. This might get fixed at
# some point, but for now this script runs this

source $UNPACK_ENV_DIR/activate.sh
export PREFIX=$CONDA_PREFIX
for i in $CONDA_PREFIX/bin/.*-post-link.sh; do
    bash $i;
done
