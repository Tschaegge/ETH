package ch.ethz.rse.integration.tests;
// DISABLED
import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY UNSAFE
// FITS_IN_RESERVE SAFE

public class Basic_IF_TestGE_para {

  public static void m1(int j) {
    Store s = new Store(2, 4);
   
    if(j>=2){
      s.get_delivery(2);
    } else {
      s.get_delivery(3);
    }
  }
}
