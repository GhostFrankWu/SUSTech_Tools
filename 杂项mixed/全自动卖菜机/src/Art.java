import javax.swing.*;
import java.awt.*;

public class Art extends JLabel {
        public Art(){
            super();
        }

    private Image offScreenImage = null;
    public void update(Graphics g) {
        if(offScreenImage == null) {
            offScreenImage = this.createImage(Screen.width, Screen.height);
        }
        Graphics gOff = offScreenImage.getGraphics();
        paint(gOff);
        g.drawImage(offScreenImage, 1, 0, null);
    }
}
