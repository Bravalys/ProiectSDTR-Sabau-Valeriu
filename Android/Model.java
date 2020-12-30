package com.rasberrypi.motiondetection;

public class Model {
    private String mImageUrl;

    public Model() {
        //empty constructor needed
    }

    public Model(String imageUrl) {
        mImageUrl = imageUrl;

    }

    public String getImageUrl() {
        return mImageUrl;
    }
    public void setImageUrl(String imageUrl) {
        mImageUrl = imageUrl;
    }
}
